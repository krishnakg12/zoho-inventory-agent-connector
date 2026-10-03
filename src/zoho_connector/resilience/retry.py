"""
Bounded exponential backoff with jitter and transient failure classification.
Safely retries transient network and server errors while rejecting client errors.
"""

import asyncio
import logging
import random
from email.utils import parsedate_to_datetime
from typing import Any, Awaitable, Callable, Optional, Set, TypeVar

import httpx

from zoho_connector.errors import (
    RateLimitError,
    UpstreamTimeoutError,
    UpstreamUnavailableError,
)

logger = logging.getLogger("zoho_connector.resilience.retry")

T = TypeVar("T")

TRANSIENT_HTTP_STATUSES: Set[int] = {429, 500, 502, 503, 504}
NON_RETRYABLE_HTTP_STATUSES: Set[int] = {400, 401, 403, 404, 409, 422}


def is_transient_status(status_code: int) -> bool:
    """Return True if status code represents a transient, retryable error."""
    return status_code in TRANSIENT_HTTP_STATUSES


def is_retryable_exception(exc: Exception) -> bool:
    """
    Determine if an exception should be retried.
    Retries:
      - 429 Too Many Requests
      - 500, 502, 503, 504 Upstream Server Errors
      - httpx network/connection/timeout errors
      - UpstreamUnavailableError, UpstreamTimeoutError, RateLimitError
    Never retries:
      - 400, 401, 403, 404, validation errors
    """
    if isinstance(exc, (UpstreamUnavailableError, UpstreamTimeoutError, RateLimitError)):
        return True

    if isinstance(exc, httpx.HTTPStatusError):
        return is_transient_status(exc.response.status_code)

    if isinstance(exc, (httpx.TimeoutException, httpx.NetworkError, httpx.ConnectError)):
        return True

    return False


def parse_retry_after(headers: Optional[httpx.Headers]) -> Optional[float]:
    """Parse Retry-After header as seconds or HTTP-date."""
    if not headers:
        return None

    raw_val = headers.get("Retry-After")
    if not raw_val:
        return None

    try:
        # Try numeric seconds
        return max(0.0, float(raw_val))
    except ValueError:
        pass

    try:
        # Try HTTP-date format
        dt = parsedate_to_datetime(raw_val)
        import datetime
        now = datetime.datetime.now(datetime.timezone.utc)
        diff = (dt - now).total_seconds()
        return max(0.0, diff)
    except Exception:
        return None


def calculate_backoff(
    attempt: int,
    base_delay: float = 0.5,
    max_delay: float = 30.0,
    jitter: bool = True,
) -> float:
    """Calculate exponential backoff with jitter."""
    delay = min(max_delay, base_delay * (2 ** attempt))
    if jitter:
        delay = random.uniform(0.5 * delay, delay)
    return delay


async def retry_with_backoff(
    operation: Callable[[], Awaitable[T]],
    max_retries: int = 3,
    base_delay: float = 0.5,
    max_delay: float = 30.0,
    op_name: str = "operation",
) -> T:
    """
    Execute async operation with bounded exponential backoff and jitter.
    Respects Retry-After header on HTTP 429 when available.
    """
    last_exc: Optional[Exception] = None

    for attempt in range(max_retries + 1):
        try:
            return await operation()
        except Exception as exc:
            last_exc = exc
            if not is_retryable_exception(exc) or attempt >= max_retries:
                raise

            retry_after: Optional[float] = None
            if isinstance(exc, httpx.HTTPStatusError) and exc.response is not None:
                retry_after = parse_retry_after(exc.response.headers)
            elif isinstance(exc, RateLimitError) and exc.retry_after_seconds:
                retry_after = float(exc.retry_after_seconds)

            if retry_after is not None:
                sleep_seconds = min(max_delay, retry_after)
            else:
                sleep_seconds = calculate_backoff(attempt, base_delay, max_delay)

            logger.warning(
                f"Transient error in {op_name} (attempt {attempt + 1}/{max_retries + 1}): {type(exc).__name__}. "
                f"Backing off for {sleep_seconds:.2f}s before retry."
            )
            await asyncio.sleep(sleep_seconds)

    if last_exc:
        raise last_exc
    raise RuntimeError(f"Retry loop completed without result or exception for {op_name}")
