"""
Normalized domain models for Zoho Inventory Sales Orders.
Maps verified Zoho API fields into compact, structured models for AI agents.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class SalesOrderLineItem(BaseModel):
    """Normalized line item within a sales order."""

    item_id: str = Field(description="Zoho Item ID.")
    name: str = Field(description="Item name / description.")
    sku: Optional[str] = Field(default=None, description="Item SKU.")
    quantity: float = Field(description="Quantity ordered.")
    rate: float = Field(description="Unit price.")
    item_total: float = Field(description="Line total (quantity * rate - discount).")
    unit: Optional[str] = Field(default=None, description="Unit of measurement.")


class SalesOrderSummary(BaseModel):
    """Compact summary of a sales order for list and search results."""

    sales_order_id: str = Field(description="Unique Zoho Sales Order ID.")
    sales_order_number: str = Field(description="Human-readable order number (e.g., SO-00042).")
    customer_id: str = Field(description="Customer ID.")
    customer_name: str = Field(description="Customer display name.")
    date: str = Field(description="Order date (YYYY-MM-DD).")
    status: str = Field(description="Order status (e.g. draft, confirmed, fulfilled, closed).")
    total: float = Field(description="Total monetary amount.")
    currency_code: Optional[str] = Field(default=None, description="Currency code.")
    shipment_date: Optional[str] = Field(default=None, description="Expected or actual shipment date.")


class SalesOrderDetail(BaseModel):
    """Detailed representation of a sales order including normalized line items."""

    sales_order_id: str = Field(description="Unique Zoho Sales Order ID.")
    sales_order_number: str = Field(description="Human-readable order number.")
    customer_id: str = Field(description="Customer ID.")
    customer_name: str = Field(description="Customer display name.")
    date: str = Field(description="Order date.")
    status: str = Field(description="Order status.")
    reference_number: Optional[str] = Field(default=None, description="Customer PO or reference number.")
    total: float = Field(description="Total order value.")
    sub_total: Optional[float] = Field(default=None, description="Subtotal before taxes.")
    tax_total: Optional[float] = Field(default=None, description="Total tax amount.")
    currency_code: Optional[str] = Field(default=None, description="Currency code.")
    delivery_method: Optional[str] = Field(default=None, description="Delivery or shipping method.")
    shipment_date: Optional[str] = Field(default=None, description="Shipment date.")
    notes: Optional[str] = Field(default=None, description="Order notes.")
    line_items: List[SalesOrderLineItem] = Field(
        default_factory=list,
        description="Line items included in the order.",
    )


def normalize_line_item(raw: Dict[str, Any]) -> SalesOrderLineItem:
    """Normalize raw line item structure from Zoho API."""
    return SalesOrderLineItem(
        item_id=str(raw.get("item_id", "")),
        name=str(raw.get("name") or raw.get("description") or ""),
        sku=raw.get("sku"),
        quantity=float(raw.get("quantity") or 0.0),
        rate=float(raw.get("rate") or 0.0),
        item_total=float(raw.get("item_total") or 0.0),
        unit=raw.get("unit"),
    )


def normalize_sales_order_summary(raw: Dict[str, Any]) -> SalesOrderSummary:
    """Project raw Zoho sales order record into SalesOrderSummary."""
    return SalesOrderSummary(
        sales_order_id=str(raw.get("salesorder_id", "")),
        sales_order_number=str(raw.get("salesorder_number", "")),
        customer_id=str(raw.get("customer_id", "")),
        customer_name=str(raw.get("customer_name", "")),
        date=str(raw.get("date", "")),
        status=str(raw.get("status") or "draft"),
        total=float(raw.get("total") or 0.0),
        currency_code=raw.get("currency_code"),
        shipment_date=raw.get("shipment_date"),
    )


def normalize_sales_order_detail(raw: Dict[str, Any]) -> SalesOrderDetail:
    """Project raw Zoho sales order record into SalesOrderDetail with line items."""
    raw_lines = raw.get("line_items", []) or []
    line_items = [normalize_line_item(item) for item in raw_lines]

    return SalesOrderDetail(
        sales_order_id=str(raw.get("salesorder_id", "")),
        sales_order_number=str(raw.get("salesorder_number", "")),
        customer_id=str(raw.get("customer_id", "")),
        customer_name=str(raw.get("customer_name", "")),
        date=str(raw.get("date", "")),
        status=str(raw.get("status") or "draft"),
        reference_number=raw.get("reference_number"),
        total=float(raw.get("total") or 0.0),
        sub_total=float(raw["sub_total"]) if raw.get("sub_total") is not None else None,
        tax_total=float(raw["tax_total"]) if raw.get("tax_total") is not None else None,
        currency_code=raw.get("currency_code"),
        delivery_method=raw.get("delivery_method"),
        shipment_date=raw.get("shipment_date"),
        notes=raw.get("notes"),
        line_items=line_items,
    )
