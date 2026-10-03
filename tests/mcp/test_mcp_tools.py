"""
MCP Tool-level tests.
Verifies tool registration, execution, input validation, and structured error responses.
"""

import json
import pytest

from zoho_connector.config import Settings
from zoho_connector.server import create_app


@pytest.fixture
def mcp_server():
    server, _ = create_app(Settings(app_mode="mock"))
    return server


@pytest.mark.asyncio
async def test_tool_registration(mcp_server):
    """Verify all 9 read-only tools are properly registered."""
    tools = await mcp_server.list_tools()
    tool_names = {t.name for t in tools}

    expected_tools = {
        "list_items",
        "get_item",
        "search_items",
        "list_sales_orders",
        "get_sales_order",
        "search_sales_orders",
        "list_contacts",
        "get_contact",
        "search_contacts",
    }
    assert expected_tools.issubset(tool_names)


@pytest.mark.asyncio
async def test_call_list_items(mcp_server):
    """Test calling list_items tool via MCP call_tool."""
    result = await mcp_server.call_tool("list_items", {"page": 1, "per_page": 2})
    assert not result.is_error
    text = result.content[0].text
    data = json.loads(text)

    assert "items" in data
    assert len(data["items"]) == 2
    assert "_untrusted_content_notice" in data


@pytest.mark.asyncio
async def test_call_get_item(mcp_server):
    """Test calling get_item tool via MCP call_tool."""
    result = await mcp_server.call_tool("get_item", {"item_id": "item_001"})
    assert not result.is_error
    data = json.loads(result.content[0].text)

    assert data["item_id"] == "item_001"
    assert data["name"] == "Ergonomic Desk Chair Pro"
    assert data["stock"]["on_hand"] == 45.0


@pytest.mark.asyncio
async def test_call_get_item_not_found(mcp_server):
    """Test calling get_item with invalid ID returns safe error dictionary."""
    result = await mcp_server.call_tool("get_item", {"item_id": "non_existent_item_999"})
    data = json.loads(result.content[0].text)

    assert data.get("error") is True
    assert data.get("code") == "NOT_FOUND"


@pytest.mark.asyncio
async def test_call_search_items(mcp_server):
    """Test calling search_items tool."""
    result = await mcp_server.call_tool("search_items", {"query": "Monitor"})
    assert not result.is_error
    data = json.loads(result.content[0].text)

    assert len(data["items"]) == 1
    assert "Monitor" in data["items"][0]["name"]


@pytest.mark.asyncio
async def test_call_list_sales_orders(mcp_server):
    """Test calling list_sales_orders tool."""
    result = await mcp_server.call_tool("list_sales_orders", {"page": 1, "per_page": 2})
    assert not result.is_error
    data = json.loads(result.content[0].text)

    assert "items" in data
    assert len(data["items"]) > 0


@pytest.mark.asyncio
async def test_call_get_sales_order(mcp_server):
    """Test calling get_sales_order tool."""
    result = await mcp_server.call_tool("get_sales_order", {"sales_order_id": "so_501"})
    assert not result.is_error
    data = json.loads(result.content[0].text)

    assert data["sales_order_number"] == "SO-00042"
    assert len(data["line_items"]) == 1
    assert data["line_items"][0]["sku"] == "FUR-CHR-001"


@pytest.mark.asyncio
async def test_call_search_sales_orders(mcp_server):
    """Test calling search_sales_orders tool."""
    result = await mcp_server.call_tool("search_sales_orders", {"order_number": "SO-00042"})
    assert not result.is_error
    data = json.loads(result.content[0].text)

    assert len(data["items"]) == 1
    assert data["items"][0]["sales_order_number"] == "SO-00042"


@pytest.mark.asyncio
async def test_call_list_contacts(mcp_server):
    """Test calling list_contacts tool."""
    result = await mcp_server.call_tool("list_contacts", {"page": 1, "per_page": 5, "contact_type": "customer"})
    assert not result.is_error
    data = json.loads(result.content[0].text)

    assert "items" in data
    assert len(data["items"]) > 0


@pytest.mark.asyncio
async def test_call_get_contact(mcp_server):
    """Test calling get_contact tool with mask_pii=True."""
    result = await mcp_server.call_tool("get_contact", {"contact_id": "contact_101", "mask_pii": True})
    assert not result.is_error
    data = json.loads(result.content[0].text)

    assert data["contact_id"] == "contact_101"
    assert "*" in data["email"]


@pytest.mark.asyncio
async def test_call_search_contacts(mcp_server):
    """Test calling search_contacts tool."""
    result = await mcp_server.call_tool("search_contacts", {"name": "Acme"})
    assert not result.is_error
    data = json.loads(result.content[0].text)

    assert len(data["items"]) == 1
    assert "Acme" in data["items"][0]["contact_name"]
