"""
Pydantic schemas and type definitions for MCP tool inputs.
Enforces schema validation before passing inputs into the service layer.
"""

from typing import Optional
from pydantic import BaseModel, Field


class ListItemsInput(BaseModel):
    page: int = Field(default=1, ge=1, description="Page number for pagination (starts at 1).")
    per_page: Optional[int] = Field(
        default=10,
        ge=1,
        le=50,
        description="Number of items to retrieve per page (max 50).",
    )
    status: Optional[str] = Field(
        default="active",
        description="Filter by item status: 'active', 'inactive', 'lowstock', or 'all'.",
    )
    sort_by: Optional[str] = Field(
        default=None,
        description="Column to sort results by (e.g., 'name', 'rate', 'created_time').",
    )


class GetItemInput(BaseModel):
    item_id: str = Field(description="Unique Zoho Item ID.")


class SearchItemsInput(BaseModel):
    query: str = Field(min_length=1, description="Keyword search query matching item name or SKU.")
    page: int = Field(default=1, ge=1, description="Page number for pagination.")
    per_page: Optional[int] = Field(default=10, ge=1, le=50, description="Number of results per page.")
    filter_by: Optional[str] = Field(
        default=None,
        description="Optional Zoho filter status (e.g. 'Status.Lowstock', 'Status.Active').",
    )


class ListSalesOrdersInput(BaseModel):
    page: int = Field(default=1, ge=1, description="Page number for pagination (starts at 1).")
    per_page: Optional[int] = Field(default=10, ge=1, le=50, description="Number of orders per page (max 50).")
    status: Optional[str] = Field(
        default=None,
        description="Filter by order status: 'draft', 'confirmed', 'fulfilled', 'closed', 'void', or 'all'.",
    )
    customer_id: Optional[str] = Field(
        default=None,
        description="Filter orders placed by a specific customer ID.",
    )
    sort_by: Optional[str] = Field(
        default=None,
        description="Column to sort results by (e.g., 'date', 'total', 'created_time').",
    )


class GetSalesOrderInput(BaseModel):
    sales_order_id: str = Field(description="Unique Zoho Sales Order ID.")


class SearchSalesOrdersInput(BaseModel):
    query: Optional[str] = Field(
        default=None,
        description="General keyword search across sales order number, customer name, and reference.",
    )
    customer_id: Optional[str] = Field(default=None, description="Exact customer ID filter.")
    customer_name: Optional[str] = Field(default=None, description="Partial customer name match.")
    order_number: Optional[str] = Field(default=None, description="Partial sales order number match.")
    page: int = Field(default=1, ge=1, description="Page number for pagination.")
    per_page: Optional[int] = Field(default=10, ge=1, le=50, description="Number of orders per page.")


class ListContactsInput(BaseModel):
    page: int = Field(default=1, ge=1, description="Page number for pagination (starts at 1).")
    per_page: Optional[int] = Field(default=10, ge=1, le=50, description="Number of contacts per page (max 50).")
    contact_type: Optional[str] = Field(
        default="customer",
        description="Classification filter: 'customer', 'vendor', or 'all'.",
    )
    status: Optional[str] = Field(
        default="active",
        description="Status filter: 'active', 'inactive', or 'all'.",
    )


class GetContactInput(BaseModel):
    contact_id: str = Field(description="Unique Zoho Contact ID.")
    mask_pii: bool = Field(
        default=False,
        description="Whether to partially mask email and phone number for privacy protection.",
    )


class SearchContactsInput(BaseModel):
    name: Optional[str] = Field(default=None, description="Partial contact or customer name match.")
    company: Optional[str] = Field(default=None, description="Partial company name match.")
    email: Optional[str] = Field(default=None, description="Partial email address match.")
    page: int = Field(default=1, ge=1, description="Page number for pagination.")
    per_page: Optional[int] = Field(default=10, ge=1, le=50, description="Number of contacts per page.")
