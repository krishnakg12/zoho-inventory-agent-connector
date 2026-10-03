"""
Deterministic Mock Client for Zoho Inventory API.
Provides realistic fictional merchant test fixtures without external network dependencies.
Strictly isolated from real client; never used as silent fallback.
"""

from typing import Any, Dict, List, Optional
from zoho_connector.errors import NotFoundError, ValidationError

MOCK_ITEMS: List[Dict[str, Any]] = [
    {
        "item_id": "item_001",
        "name": "Ergonomic Desk Chair Pro",
        "sku": "FUR-CHR-001",
        "status": "active",
        "description": "High-back mesh ergonomic office chair with adjustable lumbar support.",
        "category_name": "Office Furniture",
        "stock_on_hand": 45.0,
        "available_stock": 40.0,
        "actual_available_stock": 40.0,
        "reorder_level": 10.0,
        "rate": 299.99,
        "purchase_rate": 150.00,
        "unit": "pcs",
        "currency_code": "USD",
        "created_time": "2026-01-15T10:00:00Z",
        "last_modified_time": "2026-02-01T12:00:00Z",
    },
    {
        "item_id": "item_002",
        "name": "Ultra-wide 34-inch Monitor",
        "sku": "ELC-MON-002",
        "status": "active",
        "description": "Curved IPS WQHD display with 144Hz refresh rate.",
        "category_name": "Electronics",
        "stock_on_hand": 8.0,
        "available_stock": 3.0,
        "actual_available_stock": 3.0,
        "reorder_level": 5.0,
        "rate": 499.00,
        "purchase_rate": 320.00,
        "unit": "pcs",
        "currency_code": "USD",
        "created_time": "2026-01-20T11:00:00Z",
        "last_modified_time": "2026-02-15T15:30:00Z",
    },
    {
        "item_id": "item_003",
        "name": "Mechanical Keyboard RGB",
        "sku": "ELC-KEY-003",
        "status": "active",
        "description": "Tenkeyless mechanical gaming keyboard with hot-swappable red switches.",
        "category_name": "Electronics",
        "stock_on_hand": 2.0,
        "available_stock": 1.0,
        "actual_available_stock": 1.0,
        "reorder_level": 5.0,
        "rate": 129.50,
        "purchase_rate": 65.00,
        "unit": "pcs",
        "currency_code": "USD",
        "created_time": "2026-01-22T09:30:00Z",
        "last_modified_time": "2026-02-28T16:00:00Z",
    },
    {
        "item_id": "item_004",
        "name": "USB-C Braided Cable 2M",
        "sku": "ACC-CBL-004",
        "status": "active",
        "description": "100W Power Delivery durable nylon braided charging & data cable.",
        "category_name": "Accessories",
        "stock_on_hand": 250.0,
        "available_stock": 240.0,
        "actual_available_stock": 240.0,
        "reorder_level": 50.0,
        "rate": 19.99,
        "purchase_rate": 4.50,
        "unit": "pcs",
        "currency_code": "USD",
        "created_time": "2026-01-10T08:00:00Z",
        "last_modified_time": "2026-02-20T14:00:00Z",
    },
    {
        "item_id": "item_005",
        "name": "Noise-Cancelling Wireless Headphones",
        "sku": "AUD-HDP-005",
        "status": "active",
        "description": "Over-ear active noise cancellation bluetooth headphones with 40h battery.",
        "category_name": "Audio",
        "stock_on_hand": 0.0,
        "available_stock": 0.0,
        "actual_available_stock": 0.0,
        "reorder_level": 15.0,
        "rate": 249.00,
        "purchase_rate": 130.00,
        "unit": "pcs",
        "currency_code": "USD",
        "created_time": "2026-02-05T14:20:00Z",
        "last_modified_time": "2026-03-01T10:15:00Z",
    },
    {
        "item_id": "item_006",
        "name": "Standing Desk Dual Motor 60-inch",
        "sku": "FUR-DSK-006",
        "status": "active",
        "description": "Electric height-adjustable sit-stand desk with bamboo top.",
        "category_name": "Office Furniture",
        "stock_on_hand": 12.0,
        "available_stock": 10.0,
        "actual_available_stock": 10.0,
        "reorder_level": 5.0,
        "rate": 599.00,
        "purchase_rate": 340.00,
        "unit": "pcs",
        "currency_code": "USD",
        "created_time": "2026-02-10T16:00:00Z",
        "last_modified_time": "2026-03-02T11:00:00Z",
    },
    {
        "item_id": "item_007",
        "name": "Legacy Office Lamp v1",
        "sku": "LGT-LMP-007",
        "status": "inactive",
        "description": "Discontinued halogen desk lamp.",
        "category_name": "Lighting",
        "stock_on_hand": 0.0,
        "available_stock": 0.0,
        "actual_available_stock": 0.0,
        "reorder_level": 0.0,
        "rate": 45.00,
        "purchase_rate": 20.00,
        "unit": "pcs",
        "currency_code": "USD",
        "created_time": "2025-06-01T09:00:00Z",
        "last_modified_time": "2025-12-01T10:00:00Z",
    },
]

MOCK_CONTACTS: List[Dict[str, Any]] = [
    {
        "contact_id": "contact_101",
        "contact_name": "Acme Retail Enterprises",
        "company_name": "Acme Corp",
        "contact_type": "customer",
        "status": "active",
        "email": "billing@acmeretail.example.com",
        "phone": "+1-555-0199",
        "outstanding_receivable_amount": 1499.50,
        "outstanding_payable_amount": 0.0,
        "currency_code": "USD",
        "billing_address": {"city": "Austin", "country": "USA"},
        "created_time": "2026-01-05T09:00:00Z",
    },
    {
        "contact_id": "contact_102",
        "contact_name": "John Miller",
        "company_name": "Global Logistics Hub",
        "contact_type": "customer",
        "status": "active",
        "email": "jmiller@globallogistics.example.com",
        "phone": "+1-555-0144",
        "outstanding_receivable_amount": 0.0,
        "outstanding_payable_amount": 0.0,
        "currency_code": "USD",
        "billing_address": {"city": "Chicago", "country": "USA"},
        "created_time": "2026-01-12T14:30:00Z",
    },
    {
        "contact_id": "contact_103",
        "contact_name": "Sarah Jenkins",
        "company_name": "Apex Office Supplies",
        "contact_type": "vendor",
        "status": "active",
        "email": "sarah@apexsupplies.example.com",
        "phone": "+1-555-0177",
        "outstanding_receivable_amount": 0.0,
        "outstanding_payable_amount": 4500.00,
        "currency_code": "USD",
        "billing_address": {"city": "Seattle", "country": "USA"},
        "created_time": "2026-01-18T10:00:00Z",
    },
    {
        "contact_id": "contact_104",
        "contact_name": "Beta Electronics Ltd",
        "company_name": "Beta Electronics",
        "contact_type": "customer",
        "status": "active",
        "email": "orders@betaelec.example.com",
        "phone": "+1-555-0122",
        "outstanding_receivable_amount": 3250.00,
        "outstanding_payable_amount": 0.0,
        "currency_code": "USD",
        "billing_address": {"city": "San Jose", "country": "USA"},
        "created_time": "2026-02-01T15:00:00Z",
    },
]

MOCK_SALES_ORDERS: List[Dict[str, Any]] = [
    {
        "salesorder_id": "so_501",
        "salesorder_number": "SO-00042",
        "customer_id": "contact_101",
        "customer_name": "Acme Retail Enterprises",
        "date": "2026-03-01",
        "status": "confirmed",
        "reference_number": "PO-99120",
        "total": 1499.50,
        "sub_total": 1499.50,
        "tax_total": 0.0,
        "currency_code": "USD",
        "delivery_method": "FedEx Ground",
        "shipment_date": "2026-03-05",
        "notes": "Deliver to Building B loading dock.",
        "line_items": [
            {
                "item_id": "item_001",
                "name": "Ergonomic Desk Chair Pro",
                "sku": "FUR-CHR-001",
                "quantity": 5.0,
                "rate": 299.90,
                "item_total": 1499.50,
                "unit": "pcs",
            }
        ],
    },
    {
        "salesorder_id": "so_502",
        "salesorder_number": "SO-00043",
        "customer_id": "contact_102",
        "customer_name": "John Miller",
        "date": "2026-03-02",
        "status": "fulfilled",
        "reference_number": "PO-44811",
        "total": 998.00,
        "sub_total": 998.00,
        "tax_total": 0.0,
        "currency_code": "USD",
        "delivery_method": "Standard Courier",
        "shipment_date": "2026-03-03",
        "notes": "Left with reception.",
        "line_items": [
            {
                "item_id": "item_002",
                "name": "Ultra-wide 34-inch Monitor",
                "sku": "ELC-MON-002",
                "quantity": 2.0,
                "rate": 499.00,
                "item_total": 998.00,
                "unit": "pcs",
            }
        ],
    },
    {
        "salesorder_id": "so_503",
        "salesorder_number": "SO-00044",
        "customer_id": "contact_101",
        "customer_name": "Acme Retail Enterprises",
        "date": "2026-03-10",
        "status": "draft",
        "reference_number": "QUOTE-781",
        "total": 259.00,
        "sub_total": 259.00,
        "tax_total": 0.0,
        "currency_code": "USD",
        "delivery_method": "Standard Delivery",
        "shipment_date": "2026-03-15",
        "notes": "Awaiting customer purchase order confirmation.",
        "line_items": [
            {
                "item_id": "item_003",
                "name": "Mechanical Keyboard RGB",
                "sku": "ELC-KEY-003",
                "quantity": 2.0,
                "rate": 129.50,
                "item_total": 259.00,
                "unit": "pcs",
            }
        ],
    },
    {
        "salesorder_id": "so_504",
        "salesorder_number": "SO-00045",
        "customer_id": "contact_104",
        "customer_name": "Beta Electronics Ltd",
        "date": "2026-03-12",
        "status": "confirmed",
        "reference_number": "BETA-2026-03",
        "total": 3254.87,
        "sub_total": 3254.87,
        "tax_total": 0.0,
        "currency_code": "USD",
        "delivery_method": "Freight Express",
        "shipment_date": "2026-03-18",
        "notes": "Palletized delivery requested.",
        "line_items": [
            {
                "item_id": "item_006",
                "name": "Standing Desk Dual Motor 60-inch",
                "sku": "FUR-DSK-006",
                "quantity": 5.0,
                "rate": 599.00,
                "item_total": 2995.00,
                "unit": "pcs",
            },
            {
                "item_id": "item_004",
                "name": "USB-C Braided Cable 2M",
                "sku": "ACC-CBL-004",
                "quantity": 13.0,
                "rate": 19.99,
                "item_total": 259.87,
                "unit": "pcs",
            },
        ],
    },
]


def paginate_list(
    records: List[Dict[str, Any]],
    page: int,
    per_page: int,
) -> Dict[str, Any]:
    """Helper to slice records for pagination and produce standard Zoho page_context."""
    total = len(records)
    start = (page - 1) * per_page
    end = start + per_page
    sliced = records[start:end]
    has_more = end < total

    return {
        "page_context": {
            "page": page,
            "per_page": per_page,
            "has_more_page": has_more,
            "total": total,
        },
        "records": sliced,
    }


class MockZohoClient:
    """Deterministic, offline mock client returning verified Zoho data structures."""

    def __init__(self):
        self._items = list(MOCK_ITEMS)
        self._contacts = list(MOCK_CONTACTS)
        self._sales_orders = list(MOCK_SALES_ORDERS)

    async def list_items(self, params: Dict[str, Any]) -> Dict[str, Any]:
        page = int(params.get("page", 1))
        per_page = int(params.get("per_page", 10))
        filter_by = params.get("filter_by")
        search_text = params.get("search_text", "").lower()

        filtered = self._items

        # Filter by status / filter_by
        if filter_by == "Status.Lowstock":
            filtered = [
                i for i in filtered
                if i.get("reorder_level") is not None and i["actual_available_stock"] <= i["reorder_level"]
            ]
        elif filter_by == "Status.Active":
            filtered = [i for i in filtered if i.get("status") == "active"]
        elif filter_by == "Status.Inactive":
            filtered = [i for i in filtered if i.get("status") == "inactive"]

        # Search text
        if search_text:
            filtered = [
                i for i in filtered
                if search_text in i["name"].lower() or search_text in (i.get("sku") or "").lower()
            ]

        res = paginate_list(filtered, page, per_page)
        return {
            "code": 0,
            "message": "success",
            "page_context": res["page_context"],
            "items": res["records"],
        }

    async def get_item(self, item_id: str) -> Dict[str, Any]:
        if not item_id or not item_id.strip():
            raise ValidationError("item_id must not be empty", field="item_id")
        for item in self._items:
            if item["item_id"] == item_id.strip():
                return {
                    "code": 0,
                    "message": "success",
                    "item": item,
                }
        raise NotFoundError("Item", item_id)

    async def list_sales_orders(self, params: Dict[str, Any]) -> Dict[str, Any]:
        page = int(params.get("page", 1))
        per_page = int(params.get("per_page", 10))
        status = params.get("status")
        customer_id = params.get("customer_id")
        customer_name_contains = params.get("customer_name_contains", "").lower()
        search_text = params.get("search_text", "").lower()
        so_num = params.get("salesorder_number_contains", "").lower()

        filtered = self._sales_orders

        if status:
            filtered = [so for so in filtered if so.get("status") == status.lower()]
        if customer_id:
            filtered = [so for so in filtered if so.get("customer_id") == customer_id]
        if customer_name_contains:
            filtered = [so for so in filtered if customer_name_contains in so.get("customer_name", "").lower()]
        if so_num:
            filtered = [so for so in filtered if so_num in so.get("salesorder_number", "").lower()]
        if search_text:
            filtered = [
                so for so in filtered
                if search_text in so.get("salesorder_number", "").lower()
                or search_text in so.get("customer_name", "").lower()
                or search_text in (so.get("reference_number") or "").lower()
            ]

        res = paginate_list(filtered, page, per_page)
        return {
            "code": 0,
            "message": "success",
            "page_context": res["page_context"],
            "salesorders": res["records"],
        }

    async def get_sales_order(self, sales_order_id: str) -> Dict[str, Any]:
        if not sales_order_id or not sales_order_id.strip():
            raise ValidationError("sales_order_id must not be empty", field="sales_order_id")
        for so in self._sales_orders:
            if so["salesorder_id"] == sales_order_id.strip():
                return {
                    "code": 0,
                    "message": "success",
                    "salesorder": so,
                }
        raise NotFoundError("SalesOrder", sales_order_id)

    async def list_contacts(self, params: Dict[str, Any]) -> Dict[str, Any]:
        page = int(params.get("page", 1))
        per_page = int(params.get("per_page", 10))
        contact_type = params.get("contact_type")
        status = params.get("status")
        name_contains = params.get("contact_name_contains", "").lower()
        company_contains = params.get("company_name_contains", "").lower()
        email_contains = params.get("email_contains", "").lower()

        filtered = self._contacts

        if contact_type and contact_type.lower() != "all":
            filtered = [c for c in filtered if c.get("contact_type") == contact_type.lower()]
        if status and status.lower() != "all":
            filtered = [c for c in filtered if c.get("status") == status.lower()]
        if name_contains:
            filtered = [c for c in filtered if name_contains in c.get("contact_name", "").lower()]
        if company_contains:
            filtered = [c for c in filtered if company_contains in (c.get("company_name") or "").lower()]
        if email_contains:
            filtered = [c for c in filtered if email_contains in (c.get("email") or "").lower()]

        res = paginate_list(filtered, page, per_page)
        return {
            "code": 0,
            "message": "success",
            "page_context": res["page_context"],
            "contacts": res["records"],
        }

    async def get_contact(self, contact_id: str) -> Dict[str, Any]:
        if not contact_id or not contact_id.strip():
            raise ValidationError("contact_id must not be empty", field="contact_id")
        for contact in self._contacts:
            if contact["contact_id"] == contact_id.strip():
                return {
                    "code": 0,
                    "message": "success",
                    "contact": contact,
                }
        raise NotFoundError("Contact", contact_id)

    async def close(self) -> None:
        pass
