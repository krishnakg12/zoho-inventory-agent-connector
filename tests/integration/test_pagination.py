"""
Integration tests for pagination semantics, bounded retrieval, and context-window protection.
"""

import pytest

from zoho_connector.clients.mock_client import MockZohoClient
from zoho_connector.config import Settings
from zoho_connector.services.items import ItemService


@pytest.fixture
def mock_item_service():
    settings = Settings(
        app_mode="mock",
        default_page_size=2,
        max_page_size=4,
        max_response_bytes=65536,
    )
    client = MockZohoClient()
    return ItemService(client=client, settings=settings)


@pytest.mark.asyncio
async def test_pagination_first_page(mock_item_service):
    """Test first page has has_more=True."""
    res = await mock_item_service.list_items(page=1, per_page=2, status="all")
    assert res.pagination.page == 1
    assert len(res.items) == 2
    assert res.pagination.has_more is True
    assert not res.truncation.is_truncated


@pytest.mark.asyncio
async def test_pagination_middle_page(mock_item_service):
    """Test middle page navigation."""
    res = await mock_item_service.list_items(page=2, per_page=2, status="all")
    assert res.pagination.page == 2
    assert len(res.items) == 2
    assert res.pagination.has_more is True


@pytest.mark.asyncio
async def test_pagination_final_page(mock_item_service):
    """Test final page has has_more=False."""
    # 7 total mock items, per_page=2 -> page 4 has 1 item and has_more=False
    res = await mock_item_service.list_items(page=4, per_page=2, status="all")
    assert res.pagination.page == 4
    assert len(res.items) == 1
    assert res.pagination.has_more is False


@pytest.mark.asyncio
async def test_pagination_bounded_retrieval(mock_item_service):
    """If caller requests 100 items, per_page should be bounded to max_page_size (4)."""
    res = await mock_item_service.list_items(page=1, per_page=100, status="all")
    assert res.pagination.per_page == 4
    assert len(res.items) <= 4


@pytest.mark.asyncio
async def test_context_window_truncation():
    """
    Test that if serialized payload exceeds max_response_bytes,
    the response is trimmed and explicit truncation metadata is provided.
    """
    # Set a tiny byte budget of 400 bytes so that returning multiple items exceeds budget
    tiny_budget_settings = Settings(
        app_mode="mock",
        default_page_size=5,
        max_page_size=10,
        max_response_bytes=400,
    )
    client = MockZohoClient()
    service = ItemService(client=client, settings=tiny_budget_settings)

    res = await service.list_items(page=1, per_page=5, status="all")

    assert res.truncation.is_truncated is True
    assert "context budget" in res.truncation.truncated_reason
    assert res.truncation.next_page_instruction is not None
    assert len(res.items) < 5
