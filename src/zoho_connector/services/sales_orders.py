"""
Service layer for Zoho Inventory Sales Orders.
Handles argument normalization, field projection, and context-window protection.
"""

from typing import Any, Dict, Optional

from zoho_connector.clients.base import ZohoClientProtocol
from zoho_connector.config import Settings
from zoho_connector.errors import NotFoundError, ValidationError
from zoho_connector.models.common import BoundedListResponse
from zoho_connector.models.sales_order import (
    SalesOrderDetail,
    SalesOrderSummary,
    normalize_sales_order_detail,
    normalize_sales_order_summary,
)
from zoho_connector.services.base import BaseDataService

VALID_SO_STATUSES = {"draft", "confirmed", "fulfilled", "closed", "void", "all"}


class SalesOrderService(BaseDataService):
    """Manages business operations for Zoho Inventory Sales Orders."""

    def __init__(self, client: ZohoClientProtocol, settings: Settings):
        super().__init__(settings=settings)
        self.client = client

    async def list_sales_orders(
        self,
        page: Optional[int] = 1,
        per_page: Optional[int] = None,
        status: Optional[str] = None,
        customer_id: Optional[str] = None,
        sort_by: Optional[str] = None,
    ) -> BoundedListResponse[SalesOrderSummary]:
        """Retrieve paginated sales orders."""
        page_num, page_size = self.normalize_pagination_params(page, per_page)

        params: Dict[str, Any] = {
            "page": page_num,
            "per_page": page_size,
        }

        if status and status.lower() != "all":
            norm_status = status.strip().lower()
            if norm_status not in VALID_SO_STATUSES:
                raise ValidationError(
                    f"Invalid sales order status '{status}'. Allowed: {list(VALID_SO_STATUSES)}",
                    field="status",
                )
            params["status"] = norm_status

        if customer_id:
            params["customer_id"] = customer_id.strip()

        if sort_by:
            params["sort_column"] = sort_by.strip()

        raw_response = await self.client.list_sales_orders(params)
        raw_orders = raw_response.get("salesorders", [])
        page_ctx = raw_response.get("page_context", {})

        summaries = [normalize_sales_order_summary(so) for so in raw_orders]

        return self.build_bounded_response(
            items=summaries,
            page=page_num,
            per_page=page_size,
            has_more_upstream=page_ctx.get("has_more_page", False),
            total_count=page_ctx.get("total"),
            item_type_label="sales orders",
        )

    async def get_sales_order(self, sales_order_id: str) -> SalesOrderDetail:
        """Retrieve detailed sales order information including line items."""
        if not sales_order_id or not sales_order_id.strip():
            raise ValidationError("sales_order_id must be provided and non-empty", field="sales_order_id")

        raw_response = await self.client.get_sales_order(sales_order_id.strip())
        raw_order = raw_response.get("salesorder")
        if not raw_order:
            raise NotFoundError("SalesOrder", sales_order_id)

        return normalize_sales_order_detail(raw_order)

    async def search_sales_orders(
        self,
        query: Optional[str] = None,
        customer_id: Optional[str] = None,
        customer_name: Optional[str] = None,
        order_number: Optional[str] = None,
        page: Optional[int] = 1,
        per_page: Optional[int] = None,
    ) -> BoundedListResponse[SalesOrderSummary]:
        """Search sales orders by keyword, customer, or order number."""
        if not any([query, customer_id, customer_name, order_number]):
            raise ValidationError(
                "At least one search filter (query, customer_id, customer_name, order_number) must be specified."
            )

        page_num, page_size = self.normalize_pagination_params(page, per_page)

        params: Dict[str, Any] = {
            "page": page_num,
            "per_page": page_size,
        }

        if query:
            params["search_text"] = query.strip()
        if customer_id:
            params["customer_id"] = customer_id.strip()
        if customer_name:
            params["customer_name_contains"] = customer_name.strip()
        if order_number:
            params["salesorder_number_contains"] = order_number.strip()

        raw_response = await self.client.list_sales_orders(params)
        raw_orders = raw_response.get("salesorders", [])
        page_ctx = raw_response.get("page_context", {})

        summaries = [normalize_sales_order_summary(so) for so in raw_orders]

        return self.build_bounded_response(
            items=summaries,
            page=page_num,
            per_page=page_size,
            has_more_upstream=page_ctx.get("has_more_page", False),
            total_count=page_ctx.get("total"),
            item_type_label="sales orders",
        )
