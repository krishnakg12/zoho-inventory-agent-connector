"""
OAuth 2.0 Token Manager for Zoho Inventory API.
Handles token caching, proactive refresh, concurrency locks against stampedes,
and credential protection.
"""

import asyncio
import logging
import time
from typing import Optional

import httpx

from zoho_connector.config import Settings
from zoho_connector.errors import AuthenticationError

logger = logging.getLogger("zoho_connector.auth.oauth")


class OAuthTokenManager:
    """
    Manages Zoho OAuth 2.0 access token lifecycle.
    Ensures safe concurrent refreshes with mutual exclusion locking.
    """

    def __init__(
        self,
        settings: Settings,
        http_client: Optional[httpx.AsyncClient] = None,
        expiry_buffer_seconds: int = 300,
    ):
        self.client_id = settings.zoho_client_id
        self.client_secret = settings.zoho_client_secret
        self.refresh_token = settings.zoho_refresh_token
        self.accounts_url = settings.zoho_accounts_url.rstrip("/")
        self.expiry_buffer_seconds = expiry_buffer_seconds

        self._http_client = http_client
        self._owns_http_client = http_client is None
        self._access_token: Optional[str] = None
        self._expires_at: float = 0.0
        self._refresh_lock = asyncio.Lock()

    async def _get_client(self) -> httpx.AsyncClient:
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(timeout=10.0)
            self._owns_http_client = True
        return self._http_client

    def is_token_valid(self) -> bool:
        """Check if current access token is present and not near expiry."""
        if not self._access_token:
            return False
        return time.time() < (self._expires_at - self.expiry_buffer_seconds)

    async def get_access_token(self) -> str:
        """
        Retrieve a valid access token.
        Uses double-checked locking to prevent simultaneous refresh requests.
        """
        # Fast path: cached and still valid
        if self.is_token_valid():
            return self._access_token  # type: ignore[return-value]

        # Slow path: acquire refresh lock
        async with self._refresh_lock:
            # Re-check inside lock: another coroutine might have completed refresh while we waited
            if self.is_token_valid():
                return self._access_token  # type: ignore[return-value]

            await self._refresh_token()
            return self._access_token  # type: ignore[return-value]

    async def _refresh_token(self) -> None:
        """Execute OAuth token refresh against Zoho Accounts server."""
        if not self.client_id or not self.client_secret or not self.refresh_token:
            raise AuthenticationError(
                "Missing OAuth credentials (client_id, client_secret, or refresh_token). "
                "Ensure environment variables are properly configured."
            )

        token_endpoint = f"{self.accounts_url}/oauth/v2/token"
        payload = {
            "refresh_token": self.refresh_token,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "refresh_token",
        }

        logger.info("Initiating Zoho OAuth token refresh pipeline...")
        client = await self._get_client()

        try:
            response = await client.post(token_endpoint, data=payload)
        except (httpx.TimeoutException, httpx.NetworkError) as e:
            logger.error("Network error during OAuth token refresh")
            raise AuthenticationError("Network failure while contacting Zoho Accounts OAuth service.") from e

        if response.status_code != 200:
            logger.error(f"OAuth token rotation failed with status {response.status_code}")
            raise AuthenticationError(
                f"Zoho OAuth token refresh failed with HTTP {response.status_code}."
            )

        try:
            data = response.json()
        except Exception as e:
            raise AuthenticationError("Invalid JSON returned from Zoho OAuth endpoint.") from e

        if "error" in data:
            error_code = data.get("error")
            logger.error(f"OAuth token rotation rejected with error: {error_code}")
            raise AuthenticationError(
                f"Zoho OAuth server rejected refresh request: {error_code}"
            )

        access_token = data.get("access_token")
        if not access_token:
            raise AuthenticationError("Zoho OAuth response missing access_token field.")

        expires_in = int(data.get("expires_in", 3600))
        self._access_token = access_token
        self._expires_at = time.time() + expires_in
        logger.info(f"Successfully refreshed and cached new Zoho access token (valid for {expires_in}s).")

    def invalidate_token(self) -> None:
        """Invalidate currently cached access token (e.g. after receiving 401)."""
        self._access_token = None
        self._expires_at = 0.0

    async def close(self) -> None:
        """Close internal HTTP client if owned by this manager."""
        if self._owns_http_client and self._http_client is not None:
            await self._http_client.aclose()
            self._http_client = None
