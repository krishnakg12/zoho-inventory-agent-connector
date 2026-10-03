"""
Unit tests for retry logic and backoff with jitter.
"""

import asyncio
from unittest.mock import AsyncMock
import httpx
import pytest

from zoho_connector.errors import (
    AuthenticationError,
    RateLimitError,
    UpstreamUnavailableError,
)
from zoho_connector.resilience.retry import (
    calculate_backoff,
    is_retryable_exception,
    is_transient_status,
    parse_retry_after,
    retry_with_backoff,
)


def test_transient_status_detection():
    assert is_transient_status(429)
    assert is_transient_status(500)
    assert is_transient_status(502)
    assert is_transient_status(503)
    assert is_transient_status(504)

    assert not is_transient_status(200)
    assert not is_transient_status(400)
    assert not is_transient_status(401)
    assert not is_transient_status(403)
    assert not is_transient_status(404)


def test_retryable_exception_detection():
    assert is_retryable_exception(UpstreamUnavailableError("Down"))
    assert is_retryable_exception(RateLimitError("Limit"))
    assert is_retryable_exception(httpx.ConnectError("Connection failed"))
    assert is_retryable_exception(httpx.ReadTimeout("Timeout"))

    # Non-retryable
    assert not is_retryable_exception(AuthenticationError("Auth failed"))
    assert not is_retryable_exception(ValueError("Bad value"))


def test_parse_retry_after():
    headers = httpx.Headers({"Retry-After": "42"})
    assert parse_retry_after(headers) == 42.0

    empty_headers = httpx.Headers({})
    assert parse_retry_after(empty_headers) is None


def test_calculate_backoff():
    # Attempt 0: base_delay=0.5 -> 0.25 to 0.5 with jitter
    d0 = calculate_backoff(0, base_delay=0.5, max_delay=10.0, jitter=True)
    assert 0.25 <= d0 <= 0.5

    # Attempt 1: 0.5 to 1.0
    d1 = calculate_backoff(1, base_delay=0.5, max_delay=10.0, jitter=True)
    assert 0.5 <= d1 <= 1.0

    # Max delay cap
    d_capped = calculate_backoff(10, base_delay=1.0, max_delay=5.0, jitter=False)
    assert d_capped == 5.0


@pytest.mark.asyncio
async def test_retry_success_after_transient_failures():
    """Operation that fails twice with 503 then succeeds should return result."""
    attempts = 0

    async def flaky_op():
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            raise UpstreamUnavailableError("Server error", status_code=503)
        return "success_result"

    res = await retry_with_backoff(
        flaky_op,
        max_retries=3,
        base_delay=0.01,
        max_delay=0.1,
    )
    assert res == "success_result"
    assert attempts == 3


@pytest.mark.asyncio
async def test_retry_non_retryable_immediate_fail():
    """Non-retryable exception must not be retried."""
    attempts = 0

    async def client_error_op():
        nonlocal attempts
        attempts += 1
        raise AuthenticationError("Bad token")

    with pytest.raises(AuthenticationError):
        await retry_with_backoff(
            client_error_op,
            max_retries=3,
            base_delay=0.01,
        )

    assert attempts == 1


@pytest.mark.asyncio
async def test_retry_exhaustion():
    """Transient error that persists beyond max_retries should raise."""
    attempts = 0

    async def permanent_failure_op():
        nonlocal attempts
        attempts += 1
        raise UpstreamUnavailableError("Down")

    with pytest.raises(UpstreamUnavailableError):
        await retry_with_backoff(
            permanent_failure_op,
            max_retries=2,
            base_delay=0.01,
        )

    # 1 initial + 2 retries = 3 attempts total
    assert attempts == 3
