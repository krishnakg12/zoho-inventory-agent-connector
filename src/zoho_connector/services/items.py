"""
Service layer for Zoho Inventory Items.
Handles argument normalization, field projection, and context-window protection.
"""

from typing import Any, Dict, Optional

from zoho_connector.clients.base import ZohoClientProtocol
from zoho_connector.config import Settings
from zoho_connector.errors import ValidationError
from zoho_connector.models.common import BoundedListResponse
from zoho_connector.models.item import (
    ItemDetail,
    ItemSummary,
    normalize_item_detail,
    normalize_item_summary,
)
from zoho_connector.services.base import BaseDataService

# Status mapping for Zoho Inventory filter_by
STATUS_FILTER_MAP = {
    "all": "Status.All",
    "active": "Status.Active",
    "inactive": "Status.Inactive",
    "lowstock": "Status.Lowstock",
    "low_stock": "Status.Lowstock",
}


class ItemService(BaseDataService):
    """Manages business operations for Zoho Inventory Items."""

    def __init__(self, client: ZohoClientProtocol, settings: Settings):
        super().__init__(settings=settings)
        self.client = client

    async def list_items(
        self,
        page: Optional[int] = 1,
        per_page: Optional[int] = None,
        status: Optional[str] = "active",
        sort_by: Optional[str] = None,
    ) -> BoundedListResponse[ItemSummary]:
        """Retrieve paginated inventory items."""
        page_num, page_size = self.normalize_pagination_params(page, per_page)

        params: Dict[str, Any] = {
            "page": page_num,
            "per_page": page_size,
        }

        if status:
            norm_status = status.strip().lower()
            if norm_status in STATUS_FILTER_MAP:
                params["filter_by"] = STATUS_FILTER_MAP[norm_status]
            elif norm_status.startswith("status."):
                params["filter_by"] = status
            else:
                valid = list(STATUS_FILTER_MAP.keys())
                raise ValidationError(
                    f"Invalid item status '{status}'. Allowed options: {valid}",
                    field="status",
                )

        if sort_by:
            params["sort_column"] = sort_by.strip()

        raw_response = await self.client.list_items(params)
        raw_items = raw_response.get("items", [])
        page_ctx = raw_response.get("page_context", {})

        summaries = [normalize_item_summary(item) for item in raw_items]

        return self.build_bounded_response(
            items=summaries,
            page=page_num,
            per_page=page_size,
            has_more_upstream=page_ctx.get("has_more_page", False),
            total_count=page_ctx.get("total"),
            item_type_label="items",
        )

    async def get_item(self, item_id: str) -> ItemDetail:
        """Retrieve detailed information for a single item."""
        if not item_id or not item_id.strip():
            raise ValidationError("item_id must be provided and non-empty", field="item_id")

        raw_response = await self.client.get_item(item_id.strip())
        raw_item = raw_response.get("item")
        if not raw_item:
            from zoho_connector.errors import NotFoundError
            raise NotFoundError("Item", item_id)

        return normalize_item_detail(raw_item)

    async def search_items(
        self,
        query: str,
        page: Optional[int] = 1,
        per_page: Optional[int] = None,
        filter_by: Optional[str] = None,
    ) -> BoundedListResponse[ItemSummary]:
        """Search items by name, SKU, or keyword."""
        if not query or not query.strip():
            raise ValidationError("Search query must be provided and non-empty", field="query")

        page_num, page_size = self.normalize_pagination_params(page, per_page)

        params: Dict[str, Any] = {
            "search_text": query.strip(),
            "page": page_num,
            "per_page": page_size,
        }

        if filter_by:
            norm_filter = filter_by.strip().lower()
            if norm_filter in STATUS_FILTER_MAP:
                params["filter_by"] = STATUS_FILTER_MAP[norm_filter]
            else:
                params["filter_by"] = filter_by.strip()

        raw_response = await self.client.list_items(params)
        raw_items = raw_response.get("items", [])
        page_ctx = raw_response.get("page_context", {})

        summaries = [normalize_item_summary(item) for item in raw_items]

        return self.build_bounded_response(
            items=summaries,
            page=page_num,
            per_page=page_size,
            has_more_upstream=page_ctx.get("has_more_page", False),
            total_count=page_ctx.get("total"),
            item_type_label="items",
        )
