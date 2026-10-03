"""
Production-grade HTTP client for Zoho Inventory REST API.
Implements OAuth 2.0 token management, client-side rate limiting, concurrency limiting,
exponential backoff with jitter, error normalization, and strict tenant isolation.
"""

import logging
import time
from typing import Any, Dict, Optional

import httpx

from zoho_connector.auth.oauth import OAuthTokenManager
from zoho_connector.config import Settings
from zoho_connector.errors import (
    AuthenticationError,
    AuthorizationError,
    NotFoundError,
    RateLimitError,
    UpstreamTimeoutError,
    UpstreamUnavailableError,
    ValidationError,
    ZohoConnectorError,
)
from zoho_connector.resilience.concurrency import AsyncConcurrencyLimiter
from zoho_connector.resilience.rate_limiter import AsyncTokenBucketRateLimiter
from zoho_connector.resilience.retry import is_transient_status, parse_retry_after, retry_with_backoff

logger = logging.getLogger("zoho_connector.clients.zoho_inventory")


class ZohoInventoryClient:
    """
    Asynchronous client for interacting with Zoho Inventory API.
    Guarantees strict tenant isolation by locking requests to configured organization_id.
    """

    def __init__(
        self,
        settings: Settings,
        token_manager: Optional[OAuthTokenManager] = None,
        rate_limiter: Optional[AsyncTokenBucketRateLimiter] = None,
        concurrency_limiter: Optional[AsyncConcurrencyLimiter] = None,
        http_client: Optional[httpx.AsyncClient] = None,
    ):
        self.settings = settings
        self.base_url = settings.zoho_base_url.rstrip("/")
        self.org_id = settings.zoho_organization_id

        self.token_manager = token_manager or OAuthTokenManager(settings=settings)
        self.rate_limiter = rate_limiter or AsyncTokenBucketRateLimiter(
            requests_per_minute=settings.rate_limit_requests_per_minute
        )
        self.concurrency_limiter = concurrency_limiter or AsyncConcurrencyLimiter(
            max_concurrent=settings.max_concurrent_requests
        )

        self._http_client = http_client or httpx.AsyncClient(
            timeout=settings.request_timeout_seconds,
            limits=httpx.Limits(max_keepalive_connections=5, max_connections=20),
        )
        self._owns_http_client = http_client is None

    async def _raw_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Execute a single authenticated HTTP request with rate and concurrency limiting."""
        # 1. Proactive Rate Limiting (Token Bucket)
        await self.rate_limiter.acquire()

        # 2. Get valid OAuth access token
        token = await self.token_manager.get_access_token()

        headers = {
            "Authorization": f"Zoho-oauthtoken {token}",
            "Content-Type": "application/json;charset=UTF-8",
            "Accept": "application/json",
        }

        # 3. Tenant Isolation & Standard Pagination Context
        query_params = dict(params or {})
        query_params["organization_id"] = self.org_id
        # Include response_option=2 to request full page_context with total count
        if "response_option" not in query_params:
            query_params["response_option"] = "2"

        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        start_time = time.monotonic()

        # 4. Concurrency Limiting
        async with self.concurrency_limiter:
            try:
                response = await self._http_client.request(
                    method=method,
                    url=url,
                    headers=headers,
                    params=query_params,
                )
            except httpx.TimeoutException as exc:
                latency_ms = (time.monotonic() - start_time) * 1000
                logger.error(
                    f"HTTP timeout requesting {endpoint} ({latency_ms:.1f}ms)",
                    extra={"operation": endpoint, "latency_ms": latency_ms},
                )
                raise UpstreamTimeoutError(
                    message=f"Request to Zoho Inventory API ({endpoint}) timed out.",
                    timeout_seconds=self.settings.request_timeout_seconds,
                ) from exc
            except (httpx.NetworkError, httpx.ConnectError) as exc:
                latency_ms = (time.monotonic() - start_time) * 1000
                logger.error(
                    f"Network error requesting {endpoint}: {exc}",
                    extra={"operation": endpoint, "latency_ms": latency_ms},
                )
                raise UpstreamUnavailableError(
                    message=f"Network error communicating with Zoho Inventory API.",
                ) from exc

        latency_ms = (time.monotonic() - start_time) * 1000
        status_code = response.status_code

        logger.debug(
            f"Zoho API responded {status_code} for {endpoint} in {latency_ms:.1f}ms",
            extra={
                "operation": endpoint,
                "latency_ms": latency_ms,
                "upstream_status": status_code,
            },
        )

        # 5. Handle HTTP status codes
        if status_code == 401:
            self.token_manager.invalidate_token()
            raise AuthenticationError(
                "Zoho OAuth token expired or rejected by API (401 Unauthorized)."
            )
        elif status_code == 403:
            raise AuthorizationError(
                "Access to Zoho Inventory resource is forbidden (403 Forbidden). "
                "Verify required OAuth scopes (e.g. ZohoInventory.items.READ)."
            )
        elif status_code == 404:
            raise NotFoundError(
                resource_type="Resource",
                resource_id=endpoint,
                message=f"Zoho Inventory resource not found at endpoint: {endpoint}",
            )
        elif status_code == 429:
            retry_after = parse_retry_after(response.headers)
            raise RateLimitError(
                message=f"Zoho Inventory API rate limit exceeded (HTTP 429).",
                retry_after_seconds=int(retry_after) if retry_after else 60,
            )
        elif is_transient_status(status_code):
            raise UpstreamUnavailableError(
                message=f"Zoho Inventory API returned transient error (HTTP {status_code}).",
                status_code=status_code,
            )
        elif status_code >= 400:
            raise ZohoConnectorError(
                message=f"Zoho API returned HTTP client error {status_code}: {response.text}",
                code="HTTP_CLIENT_ERROR",
                retryable=False,
            )

        # Parse JSON
        try:
            data = response.json()
        except Exception as exc:
            raise ZohoConnectorError(
                message="Received invalid JSON response from Zoho API.",
                code="INVALID_RESPONSE_JSON",
            ) from exc

        # 6. Handle Zoho-specific error payloads returned with HTTP 200
        code = data.get("code")
        if code is not None and code != 0:
            message = data.get("message", "Unknown Zoho API error")
            if code == 45:
                raise RateLimitError(
                    message=f"Zoho rate limit error: {message}",
                    retry_after_seconds=60,
                )
            elif code in (1002, 14, 57):
                self.token_manager.invalidate_token()
                raise AuthenticationError(f"Zoho authentication error ({code}): {message}")
            elif code in (1000, 1001, 4):
                raise NotFoundError(
                    resource_type="Resource",
                    resource_id=endpoint,
                    message=f"Zoho resource not found ({code}): {message}",
                )
            elif code == 2:
                raise AuthorizationError(f"Zoho authorization error ({code}): {message}")
            elif code == 36000:
                raise ValidationError(message=f"Zoho validation error: {message}")
            else:
                raise ZohoConnectorError(
                    message=f"Zoho API error ({code}): {message}",
                    code=f"ZOHO_ERROR_{code}",
                )

        return data

    async def _request_with_retry(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Wrap request in bounded exponential backoff retry handler."""
        return await retry_with_backoff(
            operation=lambda: self._raw_request(method, endpoint, params),
            max_retries=self.settings.max_retries,
            op_name=f"{method} {endpoint}",
        )

    # -------------------------------------------------------------------------
    # Public Read-Only Operations (Protocol implementation)
    # -------------------------------------------------------------------------

    async def list_items(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List items via GET /inventory/v1/items."""
        return await self._request_with_retry("GET", "items", params)

    async def get_item(self, item_id: str) -> Dict[str, Any]:
        """Fetch item by ID via GET /inventory/v1/items/{item_id}."""
        if not item_id or not item_id.strip():
            raise ValidationError("item_id must not be empty", field="item_id")
        return await self._request_with_retry("GET", f"items/{item_id.strip()}")

    async def list_sales_orders(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List sales orders via GET /inventory/v1/salesorders."""
        return await self._request_with_retry("GET", "salesorders", params)

    async def get_sales_order(self, sales_order_id: str) -> Dict[str, Any]:
        """Fetch sales order by ID via GET /inventory/v1/salesorders/{sales_order_id}."""
        if not sales_order_id or not sales_order_id.strip():
            raise ValidationError("sales_order_id must not be empty", field="sales_order_id")
        return await self._request_with_retry("GET", f"salesorders/{sales_order_id.strip()}")

    async def list_contacts(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List contacts via GET /inventory/v1/contacts."""
        return await self._request_with_retry("GET", "contacts", params)

    async def get_contact(self, contact_id: str) -> Dict[str, Any]:
        """Fetch contact by ID via GET /inventory/v1/contacts/{contact_id}."""
        if not contact_id or not contact_id.strip():
            raise ValidationError("contact_id must not be empty", field="contact_id")
        return await self._request_with_retry("GET", f"contacts/{contact_id.strip()}")

    async def close(self) -> None:
        """Close HTTP connections and token manager client."""
        if self._owns_http_client:
            await self._http_client.aclose()
        await self.token_manager.close()
