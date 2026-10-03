"""
Unit tests for security boundaries and controls:
- Secret redaction in logs
- Tenant organization isolation
- Read-only interface guarantees
- Strict mock isolation (never silent fallback)
"""

import io
import logging
import pytest

from zoho_connector.clients.mock_client import MockZohoClient
from zoho_connector.clients.zoho_inventory import ZohoInventoryClient
from zoho_connector.config import Settings
from zoho_connector.errors import AuthenticationError, UpstreamUnavailableError
from zoho_connector.logging import SensitiveDataFilter, redact_sensitive_data
from zoho_connector.server import create_app


def test_secret_redaction_in_log_messages():
    """Verify secrets and bearer tokens are redacted from strings."""
    sample = "Connecting with Zoho-oauthtoken 1000.secret_token_123456 and client_secret=very_secret_xyz"
    redacted = redact_sensitive_data(sample)

    assert "1000.secret_token_123456" not in redacted
    assert "very_secret_xyz" not in redacted
    assert "[REDACTED]" in redacted


def test_logging_filter_redacts_record():
    """Verify logging handler filter sanitizes log records."""
    log_capture = io.StringIO()
    handler = logging.StreamHandler(log_capture)
    handler.addFilter(SensitiveDataFilter())

    logger = logging.getLogger("test_security_logger")
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)

    logger.info("Token: refresh_token=1000.super_secret_refresh_token")
    logged = log_capture.getvalue()

    assert "super_secret_refresh_token" not in logged
    assert "[REDACTED]" in logged


def test_tenant_isolation_model_cannot_override_organization():
    """Verify organization_id cannot be manipulated by tool parameters."""
    server, _ = create_app(Settings(app_mode="mock", zoho_organization_id="ORG_FIXED_999"))
    
    # Verify no tool allows passing organization_id
    tool_names = [
        "list_items", "get_item", "search_items",
        "list_sales_orders", "get_sales_order", "search_sales_orders",
        "list_contacts", "get_contact", "search_contacts",
    ]
    # No tool parameter signature accepts organization_id
    from zoho_connector.mcp import schemas
    for schema_cls in [
        schemas.ListItemsInput,
        schemas.GetItemInput,
        schemas.SearchItemsInput,
        schemas.ListSalesOrdersInput,
        schemas.GetSalesOrderInput,
        schemas.SearchSalesOrdersInput,
        schemas.ListContactsInput,
        schemas.GetContactInput,
        schemas.SearchContactsInput,
    ]:
        assert "organization_id" not in schema_cls.model_fields


def test_read_only_policy_no_mutations_available():
    """Verify only read-only query tools exist; no create/update/delete operations."""
    server, _ = create_app(Settings(app_mode="mock"))
    
    # We can inspect tools registered on server
    import asyncio
    tools = asyncio.run(server.list_tools())
    registered_names = {t.name for t in tools}

    forbidden_keywords = ["create", "update", "delete", "post", "put", "patch", "modify", "cancel"]
    for tool_name in registered_names:
        for kw in forbidden_keywords:
            assert kw not in tool_name, f"Forbidden mutation keyword '{kw}' found in tool '{tool_name}'"


def test_mock_isolation_live_mode_never_falls_back_to_mock():
    """
    Verify that in live mode, missing credentials or API failures do NOT
    silently fall back to mock data.
    """
    # 1. In live mode with placeholder credentials, it must fail configuration validation
    with pytest.raises(ValueError, match="Live mode requires valid Zoho credentials"):
        Settings(
            app_mode="live",
            zoho_organization_id="YOUR_NUMERIC_ORGANIZATION_ID",
            zoho_client_id="your_zoho_client_id_here",
            zoho_client_secret="your_zoho_client_secret_here",
            zoho_refresh_token="your_zoho_refresh_token_here",
        )

    # 2. In live mode with mock settings, create_app creates ZohoInventoryClient, NOT MockZohoClient
    live_settings = Settings(
        app_mode="live",
        zoho_organization_id="123456789",
        zoho_client_id="valid_client_id",
        zoho_client_secret="valid_client_secret",
        zoho_refresh_token="valid_refresh_token",
    )
    server, client = create_app(settings=live_settings)
    assert isinstance(client, ZohoInventoryClient)
    assert not isinstance(client, MockZohoClient)
