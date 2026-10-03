"""
Unit tests for ItemService, SalesOrderService, and ContactService.
Verifies business constraints, normalization, and bounds enforcement.
"""

import pytest

from zoho_connector.clients.mock_client import MockZohoClient
from zoho_connector.config import Settings
from zoho_connector.errors import NotFoundError, ValidationError
from zoho_connector.services.contacts import ContactService
from zoho_connector.services.items import ItemService
from zoho_connector.services.sales_orders import SalesOrderService


@pytest.fixture
def service_env():
    settings = Settings(
        app_mode="mock",
        default_page_size=5,
        max_page_size=20,
        max_response_bytes=10000,
    )
    client = MockZohoClient()
    return {
        "items": ItemService(client=client, settings=settings),
        "sales_orders": SalesOrderService(client=client, settings=settings),
        "contacts": ContactService(client=client, settings=settings),
        "settings": settings,
        "client": client,
    }


# =============================================================================
# ITEMS SERVICE TESTS
# =============================================================================

@pytest.mark.asyncio
async def test_items_list(service_env):
    srv = service_env["items"]
    res = await srv.list_items(page=1, per_page=5, status="active")
    assert len(res.items) > 0
    assert res.pagination.page == 1
    assert res.pagination.per_page == 5
    assert not res.truncation.is_truncated


@pytest.mark.asyncio
async def test_items_get_valid(service_env):
    srv = service_env["items"]
    item = await srv.get_item("item_001")
    assert item.item_id == "item_001"
    assert "Desk Chair" in item.name
    assert item.stock.on_hand == 45.0


@pytest.mark.asyncio
async def test_items_get_not_found(service_env):
    srv = service_env["items"]
    with pytest.raises(NotFoundError):
        await srv.get_item("non_existent_item_999")


@pytest.mark.asyncio
async def test_items_search(service_env):
    srv = service_env["items"]
    res = await srv.search_items(query="Keyboard")
    assert len(res.items) >= 1
    assert any("Keyboard" in item.name for item in res.items)


@pytest.mark.asyncio
async def test_items_search_empty(service_env):
    srv = service_env["items"]
    res = await srv.search_items(query="NonExistentProductZXY987")
    assert len(res.items) == 0
    assert res.pagination.total_count == 0


@pytest.mark.asyncio
async def test_items_invalid_input(service_env):
    srv = service_env["items"]
    with pytest.raises(ValidationError):
        await srv.get_item("")
    with pytest.raises(ValidationError):
        await srv.search_items("")
    with pytest.raises(ValidationError):
        await srv.list_items(status="invalid_status_xyz")


# =============================================================================
# SALES ORDERS SERVICE TESTS
# =============================================================================

@pytest.mark.asyncio
async def test_sales_orders_list(service_env):
    srv = service_env["sales_orders"]
    res = await srv.list_sales_orders(page=1, per_page=5)
    assert len(res.items) > 0
    assert res.items[0].sales_order_number.startswith("SO-")


@pytest.mark.asyncio
async def test_sales_orders_get(service_env):
    srv = service_env["sales_orders"]
    order = await srv.get_sales_order("so_501")
    assert order.sales_order_id == "so_501"
    assert order.sales_order_number == "SO-00042"
    assert len(order.line_items) == 1
    assert order.total == 1499.50


@pytest.mark.asyncio
async def test_sales_orders_search(service_env):
    srv = service_env["sales_orders"]
    # Search by order number
    res = await srv.search_sales_orders(order_number="SO-00042")
    assert len(res.items) == 1
    assert res.items[0].sales_order_number == "SO-00042"


@pytest.mark.asyncio
async def test_sales_orders_search_by_customer(service_env):
    srv = service_env["sales_orders"]
    res = await srv.search_sales_orders(customer_id="contact_101")
    assert len(res.items) >= 2


@pytest.mark.asyncio
async def test_sales_orders_invalid_input(service_env):
    srv = service_env["sales_orders"]
    with pytest.raises(ValidationError):
        await srv.get_sales_order("   ")
    with pytest.raises(ValidationError):
        # Empty search filter
        await srv.search_sales_orders()


# =============================================================================
# CONTACTS SERVICE TESTS
# =============================================================================

@pytest.mark.asyncio
async def test_contacts_list(service_env):
    srv = service_env["contacts"]
    res = await srv.list_contacts(page=1, per_page=10, contact_type="customer")
    assert len(res.items) > 0
    assert all(c.contact_type == "customer" for c in res.items)


@pytest.mark.asyncio
async def test_contacts_get(service_env):
    srv = service_env["contacts"]
    c = await srv.get_contact("contact_101", mask_pii=True)
    assert c.contact_id == "contact_101"
    assert c.outstanding_receivable_amount == 1499.50
    assert "*" in c.email  # Masked


@pytest.mark.asyncio
async def test_contacts_search(service_env):
    srv = service_env["contacts"]
    res = await srv.search_contacts(name="Acme")
    assert len(res.items) == 1
    assert "Acme" in res.items[0].contact_name


@pytest.mark.asyncio
async def test_contacts_invalid_input(service_env):
    srv = service_env["contacts"]
    with pytest.raises(ValidationError):
        await srv.get_contact("")
    with pytest.raises(ValidationError):
        await srv.search_contacts()
    with pytest.raises(ValidationError):
        await srv.list_contacts(contact_type="unsupported_type")
