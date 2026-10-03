"""
Unit tests for OAuth Token Manager.
Verifies token caching, expiry buffering, refresh logic, and concurrent stampede protection.
"""

import asyncio
import json
import time
from pathlib import Path
from unittest.mock import AsyncMock, patch

import httpx
import pytest

from zoho_connector.auth.oauth import OAuthTokenManager
from zoho_connector.config import Settings
from zoho_connector.errors import AuthenticationError


@pytest.fixture
def mock_settings():
    return Settings(
        app_mode="mock",
        zoho_organization_id="10001",
        zoho_client_id="test_client_id_123",
        zoho_client_secret="test_client_secret_xyz",
        zoho_refresh_token="test_refresh_token_abc",
        zoho_base_url="https://www.zohoapis.com/inventory/v1",
        zoho_accounts_url="https://accounts.zoho.com",
    )


@pytest.mark.asyncio
async def test_oauth_valid_refresh(mock_settings):
    """Test successful token refresh with valid credentials."""
    fixture_path = Path(__file__).parent.parent / "fixtures" / "oauth.json"
    fixture_data = json.loads(fixture_path.read_text())

    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_response = httpx.Response(
        status_code=200,
        json=fixture_data,
        request=httpx.Request("POST", "https://accounts.zoho.com/oauth/v2/token"),
    )
    mock_client.post.return_value = mock_response

    manager = OAuthTokenManager(settings=mock_settings, http_client=mock_client)
    assert not manager.is_token_valid()

    token = await manager.get_access_token()
    assert token == fixture_data["access_token"]
    assert manager.is_token_valid()
    assert mock_client.post.call_count == 1

    # Second call uses cached token without network request
    token2 = await manager.get_access_token()
    assert token2 == token
    assert mock_client.post.call_count == 1


@pytest.mark.asyncio
async def test_oauth_missing_credentials():
    """Test that missing credentials raise an AuthenticationError."""
    settings = Settings(
        app_mode="mock",
        zoho_client_id=None,
        zoho_client_secret=None,
        zoho_refresh_token=None,
    )
    manager = OAuthTokenManager(settings=settings)
    with pytest.raises(AuthenticationError, match="Missing OAuth credentials"):
        await manager.get_access_token()


@pytest.mark.asyncio
async def test_oauth_rejected_by_upstream(mock_settings):
    """Test that upstream OAuth errors (e.g. invalid_client) raise AuthenticationError."""
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_response = httpx.Response(
        status_code=200,
        json={"error": "invalid_client"},
        request=httpx.Request("POST", "https://accounts.zoho.com/oauth/v2/token"),
    )
    mock_client.post.return_value = mock_response

    manager = OAuthTokenManager(settings=mock_settings, http_client=mock_client)
    with pytest.raises(AuthenticationError, match="invalid_client"):
        await manager.get_access_token()


@pytest.mark.asyncio
async def test_oauth_concurrent_refresh_stampede_protection(mock_settings):
    """
    Test that multiple concurrent requests when token is expired
    execute only a SINGLE network refresh call due to mutex locking.
    """
    fixture_path = Path(__file__).parent.parent / "fixtures" / "oauth.json"
    fixture_data = json.loads(fixture_path.read_text())

    call_count = 0

    async def delayed_post(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        await asyncio.sleep(0.05)  # Simulate network latency
        return httpx.Response(
            status_code=200,
            json=fixture_data,
            request=httpx.Request("POST", "https://accounts.zoho.com/oauth/v2/token"),
        )

    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.post.side_effect = delayed_post

    manager = OAuthTokenManager(settings=mock_settings, http_client=mock_client)

    # Launch 10 concurrent requests for access token
    tasks = [manager.get_access_token() for _ in range(10)]
    tokens = await asyncio.gather(*tasks)

    # All 10 requests should receive the identical valid access token
    for tok in tokens:
        assert tok == fixture_data["access_token"]

    # Crucial check: Upstream endpoint was called EXACTLY ONCE
    assert call_count == 1


@pytest.mark.asyncio
async def test_oauth_invalidate_token(mock_settings):
    """Test manual invalidation resets cached token and expiry."""
    manager = OAuthTokenManager(settings=mock_settings)
    manager._access_token = "some_token"
    manager._expires_at = time.time() + 3600
    assert manager.is_token_valid()

    manager.invalidate_token()
    assert not manager.is_token_valid()
    assert manager._access_token is None
