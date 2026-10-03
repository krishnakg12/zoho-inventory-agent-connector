# System Limitations and Scope Boundaries

This document defines what the Zoho Inventory MCP Connector explicitly **does NOT solve**, establishing clear functional and operational boundaries.

---

## 1. Strictly Read-Only Operations
- **No Order Creation**: The connector cannot generate new sales orders or quote estimates in Zoho Inventory.
- **No Inventory Adjustments**: The connector cannot update stock counts, adjust quantities, write down inventory, or record stock transfers.
- **No Customer/Contact Modifications**: The connector cannot create new counterparties or edit addresses, phone numbers, or credit terms.

## 2. Single-Tenant Process Instance
- **No Runtime Tenant Switching**: Each running MCP server process is bound to a single merchant organization via `ZOHO_ORGANIZATION_ID`.
- Multi-merchant SaaS setups must run distinct connector instances per merchant organization or manage isolation at the process boundary. The AI agent cannot dynamically swap merchant IDs within a single session.

## 3. Pull-Based Architecture (No Webhooks)
- **No Push Notifications**: The connector operates purely on request-response tool calls initiated by the AI agent.
- It does not host HTTP webhook listeners for Zoho inventory status updates, order status changes, or low-stock alerts.

## 4. Not an ETL or Data Warehousing Pipeline
- **Context-Sized Retrieval**: The connector is optimized for small, targeted queries (1–50 records) tailored for LLM reasoning.
- It is **not** designed for bulk exports, database backups, or historical ledger migrations of hundreds of thousands of records. Unbounded retrieval is actively blocked by the pagination and context guards.

## 5. No Semantic Vector Search
- Search tools (`search_items`, `search_sales_orders`, `search_contacts`) rely on Zoho's keyword and prefix/contains filtering.
- The connector does not maintain a vector database, embedding index, or fuzzy semantic cache. Semantic understanding is the responsibility of the AI agent reasoning over the returned structured records.

## 6. No Direct Financial Transactions
- While the connector exposes `total`, `tax_total`, and `outstanding_receivable_amount`, it does not process financial transactions, trigger gateway charges (e.g. Razorpay, Stripe), or generate invoice receipts.

## 7. Upstream Rate Limit Ceiling
- Client-side token-bucket rate limiting operates at 60 requests/minute to ensure safety headroom.
- If other third-party integrations consume the merchant's 100 requests/minute quota upstream, the connector will receive HTTP 429 errors and back off as instructed by Zoho.
