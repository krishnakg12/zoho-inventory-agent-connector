"""
Abstract base protocol/interface for Zoho Inventory clients.
Enables clean dependency injection between real HTTP client and offline mock client.
"""

from typing import Any, Dict, Protocol, runtime_checkable


@runtime_checkable
class ZohoClientProtocol(Protocol):
    """Protocol defining the core read-only data access operations for Zoho Inventory."""

    async def list_items(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Fetch paginated items matching criteria."""
        ...

    async def get_item(self, item_id: str) -> Dict[str, Any]:
        """Fetch single item by unique ID."""
        ...

    async def list_sales_orders(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Fetch paginated sales orders matching criteria."""
        ...

    async def get_sales_order(self, sales_order_id: str) -> Dict[str, Any]:
        """Fetch single sales order by unique ID."""
        ...

    async def list_contacts(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Fetch paginated contacts matching criteria."""
        ...

    async def get_contact(self, contact_id: str) -> Dict[str, Any]:
        """Fetch single contact by unique ID."""
        ...

    async def close(self) -> None:
        """Close underlying connection resources."""
        ...
