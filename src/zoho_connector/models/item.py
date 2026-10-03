"""
Normalized domain models for Zoho Inventory Items.
Maps verified Zoho API fields into compact, structured models for AI agents.
"""

from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class ItemStock(BaseModel):
    """Normalized inventory stock levels."""

    on_hand: float = Field(default=0.0, description="Total physical quantity on hand.")
    reserved: float = Field(default=0.0, description="Quantity committed to confirmed sales orders.")
    available: float = Field(default=0.0, description="Stock available for immediate commitment/sale.")
    reorder_level: Optional[float] = Field(default=None, description="Low-stock threshold for reordering.")
    unit: Optional[str] = Field(default=None, description="Unit of measurement (e.g. pcs, kgs, boxes).")


class ItemPricing(BaseModel):
    """Normalized pricing information."""

    selling_price: float = Field(default=0.0, description="Sales rate/price.")
    purchase_price: Optional[float] = Field(default=None, description="Cost or purchase rate.")
    currency_code: Optional[str] = Field(default=None, description="Currency code (e.g. USD, INR).")


class ItemSummary(BaseModel):
    """Compact summary of an inventory item for list and search results."""

    item_id: str = Field(description="Unique Zoho Item ID.")
    name: str = Field(description="Item name.")
    sku: Optional[str] = Field(default=None, description="Stock Keeping Unit.")
    status: str = Field(default="active", description="Status (active, inactive).")
    stock: ItemStock = Field(description="Stock levels.")
    pricing: ItemPricing = Field(description="Pricing details.")


class ItemDetail(BaseModel):
    """Detailed representation of an inventory item."""

    item_id: str = Field(description="Unique Zoho Item ID.")
    name: str = Field(description="Item name.")
    sku: Optional[str] = Field(default=None, description="Stock Keeping Unit.")
    status: str = Field(default="active", description="Status (active, inactive).")
    description: Optional[str] = Field(default=None, description="Item description.")
    category_name: Optional[str] = Field(default=None, description="Product category.")
    stock: ItemStock = Field(description="Stock levels.")
    pricing: ItemPricing = Field(description="Pricing details.")
    created_time: Optional[str] = Field(default=None, description="Record creation timestamp.")
    last_modified_time: Optional[str] = Field(default=None, description="Last modification timestamp.")


def normalize_item_stock(raw: Dict[str, Any]) -> ItemStock:
    """Safely map raw Zoho stock attributes to normalized ItemStock."""
    on_hand = float(raw.get("stock_on_hand") or 0.0)
    actual_available = raw.get("actual_available_stock")
    available_stock = raw.get("available_stock")

    if actual_available is not None:
        avail = float(actual_available)
    elif available_stock is not None:
        avail = float(available_stock)
    else:
        avail = on_hand

    # Reserved stock is physical stock minus available stock
    reserved = max(0.0, on_hand - avail)
    reorder_level = raw.get("reorder_level")

    return ItemStock(
        on_hand=on_hand,
        reserved=reserved,
        available=avail,
        reorder_level=float(reorder_level) if reorder_level is not None else None,
        unit=raw.get("unit"),
    )


def normalize_item_pricing(raw: Dict[str, Any]) -> ItemPricing:
    """Safely map raw Zoho pricing attributes to normalized ItemPricing."""
    rate = float(raw.get("rate") or 0.0)
    purchase_rate = raw.get("purchase_rate")
    return ItemPricing(
        selling_price=rate,
        purchase_price=float(purchase_rate) if purchase_rate is not None else None,
        currency_code=raw.get("currency_code"),
    )


def normalize_item_summary(raw: Dict[str, Any]) -> ItemSummary:
    """Project raw Zoho item record into compact ItemSummary."""
    return ItemSummary(
        item_id=str(raw.get("item_id", "")),
        name=str(raw.get("name") or raw.get("item_name") or ""),
        sku=raw.get("sku"),
        status=str(raw.get("status") or "active"),
        stock=normalize_item_stock(raw),
        pricing=normalize_item_pricing(raw),
    )


def normalize_item_detail(raw: Dict[str, Any]) -> ItemDetail:
    """Project raw Zoho item record into ItemDetail."""
    return ItemDetail(
        item_id=str(raw.get("item_id", "")),
        name=str(raw.get("name") or raw.get("item_name") or ""),
        sku=raw.get("sku"),
        status=str(raw.get("status") or "active"),
        description=raw.get("description"),
        category_name=raw.get("category_name"),
        stock=normalize_item_stock(raw),
        pricing=normalize_item_pricing(raw),
        created_time=raw.get("created_time"),
        last_modified_time=raw.get("last_modified_time"),
    )
