# Sample Agent Queries and MCP Tool Mapping

This document illustrates how natural language merchant requests map deterministically into read-only MCP tool calls provided by the Zoho Inventory Connector.

---

## 1. Inventory & Stock Queries

### Query 1: "Which products are running low on stock?"
* **Agent Intent**: Identify items where `actual_available_stock` is less than or equal to `reorder_level`.
* **MCP Tool Call**:
  ```json
  {
    "name": "list_items",
    "arguments": {
      "status": "lowstock",
      "per_page": 10
    }
  }
  ```
* **Sample Response**: See [`sample_responses/item_low_stock.json`](file:///c:/Users/krish/OneDrive/razorpay_zoho_inventory_connector/examples/sample_responses/item_low_stock.json)

### Query 2: "Search for the 34-inch ultra-wide monitor details."
* **Agent Intent**: Retrieve specific product specifications, SKU, and exact pricing/stock split.
* **MCP Tool Call**:
  ```json
  {
    "name": "search_items",
    "arguments": {
      "query": "Monitor"
    }
  }
  ```

---

## 2. Customer & Contact Queries

### Query 3: "Lookup customer Acme Corp and their payment balance."
* **Agent Intent**: Find counterparty record and inspect outstanding accounts receivable balance.
* **Step 1 - Tool Call**:
  ```json
  {
    "name": "search_contacts",
    "arguments": {
      "name": "Acme"
    }
  }
  ```
* **Step 2 - Tool Call (PII Minimized)**:
  ```json
  {
    "name": "get_contact",
    "arguments": {
      "contact_id": "contact_101",
      "mask_pii": true
    }
  }
  ```
* **Sample Response**: See [`sample_responses/contact_lookup.json`](file:///c:/Users/krish/OneDrive/razorpay_zoho_inventory_connector/examples/sample_responses/contact_lookup.json)

---

## 3. Sales Order & Fulfillment Queries

### Query 4: "Find recent orders placed by Acme Retail Enterprises."
* **Agent Intent**: Retrieve customer order history to verify status and line items.
* **MCP Tool Call**:
  ```json
  {
    "name": "search_sales_orders",
    "arguments": {
      "customer_id": "contact_101",
      "per_page": 5
    }
  }
  ```
* **Sample Response**: See [`sample_responses/sales_orders_customer.json`](file:///c:/Users/krish/OneDrive/razorpay_zoho_inventory_connector/examples/sample_responses/sales_orders_customer.json)

### Query 5: "What items were shipped in order SO-00042?"
* **Agent Intent**: Get detailed order breakdown and line items.
* **MCP Tool Call**:
  ```json
  {
    "name": "get_sales_order",
    "arguments": {
      "sales_order_id": "so_501"
    }
  }
  ```
