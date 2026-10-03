"""
Unit tests for domain models and data normalization.
"""

from zoho_connector.models.contact import (
    mask_email,
    mask_phone,
    normalize_contact_detail,
    normalize_contact_summary,
)
from zoho_connector.models.item import (
    normalize_item_detail,
    normalize_item_pricing,
    normalize_item_stock,
    normalize_item_summary,
)
from zoho_connector.models.sales_order import (
    normalize_line_item,
    normalize_sales_order_detail,
    normalize_sales_order_summary,
)


def test_item_stock_normalization():
    raw = {
        "stock_on_hand": 50.0,
        "actual_available_stock": 42.0,
        "reorder_level": 10.0,
        "unit": "pcs",
    }
    stock = normalize_item_stock(raw)
    assert stock.on_hand == 50.0
    assert stock.available == 42.0
    assert stock.reserved == 8.0
    assert stock.reorder_level == 10.0
    assert stock.unit == "pcs"


def test_item_pricing_normalization():
    raw = {"rate": 99.95, "purchase_rate": 45.0, "currency_code": "USD"}
    pricing = normalize_item_pricing(raw)
    assert pricing.selling_price == 99.95
    assert pricing.purchase_price == 45.0
    assert pricing.currency_code == "USD"


def test_item_summary_normalization():
    raw = {
        "item_id": "item_123",
        "name": "Standing Desk",
        "sku": "DSK-01",
        "status": "active",
        "stock_on_hand": 10,
        "actual_available_stock": 8,
        "rate": 299.0,
    }
    summary = normalize_item_summary(raw)
    assert summary.item_id == "item_123"
    assert summary.name == "Standing Desk"
    assert summary.sku == "DSK-01"
    assert summary.stock.on_hand == 10.0
    assert summary.stock.available == 8.0
    assert summary.stock.reserved == 2.0
    assert summary.pricing.selling_price == 299.0


def test_sales_order_normalization():
    raw = {
        "salesorder_id": "so_123",
        "salesorder_number": "SO-001",
        "customer_id": "cust_1",
        "customer_name": "Acme Corp",
        "date": "2026-03-01",
        "status": "confirmed",
        "total": 500.0,
        "line_items": [
            {
                "item_id": "item_1",
                "name": "Widget",
                "quantity": 5,
                "rate": 100.0,
                "item_total": 500.0,
            }
        ],
    }
    so_sum = normalize_sales_order_summary(raw)
    assert so_sum.sales_order_id == "so_123"
    assert so_sum.sales_order_number == "SO-001"
    assert so_sum.total == 500.0

    so_det = normalize_sales_order_detail(raw)
    assert len(so_det.line_items) == 1
    assert so_det.line_items[0].item_id == "item_1"
    assert so_det.line_items[0].quantity == 5.0
    assert so_det.line_items[0].item_total == 500.0


def test_contact_pii_masking():
    assert mask_email("alex@example.com") == "a**x@example.com"
    assert mask_email("j@test.com") == "j*@test.com"
    assert mask_phone("+1-555-0199") == "*******0199"

    raw = {
        "contact_id": "c_1",
        "contact_name": "John Doe",
        "email": "johndoe@example.com",
        "phone": "+15551234567",
        "outstanding_receivable_amount": 150.0,
    }
    c_masked = normalize_contact_detail(raw, mask_pii=True)
    assert c_masked.email == "j*****e@example.com"
    assert c_masked.phone == "********4567"
