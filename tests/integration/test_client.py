"""
Integration tests for ZohoInventoryClient using httpx MockTransport.
Tests end-to-end HTTP pipeline including auth headers, tenant isolation, error mapping, and retries.
"""

import json
from pathlib import Path
from unittest.mock import AsyncMock

import httpx
import pytest

from zoho_connector.auth.oauth import OAuthTokenManager
from zoho_connector.clients.zoho_inventory import ZohoInventoryClient
from zoho_connector.config import Settings
from zoho_connector.errors import (
    AuthenticationError,
    AuthorizationError,
    NotFoundError,
    RateLimitError,
    UpstreamTimeoutError,
    UpstreamUnavailableError,
)
from zoho_connector.resilience.concurrency import AsyncConcurrencyLimiter
from zoho_connector.resilience.rate_limiter import AsyncTokenBucketRateLimiter


@pytest.fixture
def fixtures():
    base_dir = Path(__file__).parent.parent / "fixtures"
    return {
        "items": json.loads((base_dir / "items.json").read_text()),
        "sales_orders": json.loads((base_dir / "sales_orders.json").read_text()),
        "contacts": json.loads((base_dir / "contacts.json").read_text()),
    }


@pytest.fixture
def mock_token_manager():
    tm = AsyncMock(spec=OAuthTokenManager)
    tm.get_access_token.return_value = "mock_valid_token_123"
    return tm


@pytest.mark.asyncio
async def test_client_list_items_success(fixtures, mock_token_manager):
    """Test standard list items call includes organization_id and auth header."""
    recorded_request = None

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal recorded_request
        recorded_request = request
        return httpx.Response(200, json=fixtures["items"])

    settings = Settings(
        app_mode="mock",
        zoho_organization_id="ORG_TEST_99",
        max_retries=1,
    )
    transport = httpx.MockTransport(handler)
    http_client = httpx.AsyncClient(transport=transport)

    client = ZohoInventoryClient(
        settings=settings,
        token_manager=mock_token_manager,
        http_client=http_client,
    )

    result = await client.list_items({"page": 1, "per_page": 2})

    assert recorded_request is not None
    assert recorded_request.headers["Authorization"] == "Zoho-oauthtoken mock_valid_token_123"
    assert "organization_id=ORG_TEST_99" in str(recorded_request.url)
    assert len(result["items"]) == 2
    assert result["items"][0]["item_id"] == "item_101"


@pytest.mark.asyncio
async def test_client_401_invalidates_token(mock_token_manager):
    """HTTP 401 should invalidate token cache and raise AuthenticationError."""
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"message": "Unauthorized"})

    settings = Settings(app_mode="mock", zoho_organization_id="ORG_1", max_retries=0)
    client = ZohoInventoryClient(
        settings=settings,
        token_manager=mock_token_manager,
        http_client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),
    )

    with pytest.raises(AuthenticationError):
        await client.list_items({})

    mock_token_manager.invalidate_token.assert_called_once()


@pytest.mark.asyncio
async def test_client_403_raises_authorization_error(mock_token_manager):
    """HTTP 403 should raise AuthorizationError."""
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(403, json={"message": "Forbidden scope"})

    settings = Settings(app_mode="mock", zoho_organization_id="ORG_1", max_retries=0)
    client = ZohoInventoryClient(
        settings=settings,
        token_manager=mock_token_manager,
        http_client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),
    )

    with pytest.raises(AuthorizationError):
        await client.list_items({})


@pytest.mark.asyncio
async def test_client_404_raises_not_found(mock_token_manager):
    """HTTP 404 should raise NotFoundError."""
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, json={"message": "Item not found"})

    settings = Settings(app_mode="mock", zoho_organization_id="ORG_1", max_retries=0)
    client = ZohoInventoryClient(
        settings=settings,
        token_manager=mock_token_manager,
        http_client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),
    )

    with pytest.raises(NotFoundError):
        await client.get_item("non_existent_123")


@pytest.mark.asyncio
async def test_client_429_rate_limit(mock_token_manager):
    """HTTP 429 should raise RateLimitError with retry_after header parsed."""
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            429,
            headers={"Retry-After": "45"},
            json={"code": 45, "message": "Max call rate exceeded"},
        )

    settings = Settings(app_mode="mock", zoho_organization_id="ORG_1", max_retries=0)
    client = ZohoInventoryClient(
        settings=settings,
        token_manager=mock_token_manager,
        http_client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),
    )

    with pytest.raises(RateLimitError) as exc_info:
        await client.list_items({})

    assert exc_info.value.retry_after_seconds == 45


@pytest.mark.asyncio
async def test_client_retry_and_recovery(fixtures, mock_token_manager):
    """Client should retry on 503 and succeed on subsequent attempt."""
    attempts = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            return httpx.Response(503, text="Service Unavailable")
        return httpx.Response(200, json=fixtures["items"])

    settings = Settings(app_mode="mock", zoho_organization_id="ORG_1", max_retries=2)
    client = ZohoInventoryClient(
        settings=settings,
        token_manager=mock_token_manager,
        http_client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),
    )

    result = await client.list_items({})
    assert len(result["items"]) == 2
    assert attempts == 2
