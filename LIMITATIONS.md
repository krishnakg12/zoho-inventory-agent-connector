# System Limitations and Scope Boundaries

This document defines what the Zoho Inventory MCP Connector explicitly **does NOT solve**, establishing clear functional and operational boundaries.

---

## 1. Strictly Read-Only Operations

- **No Order Creation**: The connector cannot generate new sales orders or quote estimates in Zoho Inventory.

- **No Inventory Adjustments**: The connector cannot update stock counts, adjust quantities, write down inventory, or record stock transfers.

- **No Customer/Contact Modifications**: The connector cannot create new counterparties or edit addresses, phone numbers, or credit terms.

All exposed MCP tools are read-only.

## 2. Single-Tenant Process Instance

- **No Runtime Tenant Switching**: Each running MCP server process is bound to a single merchant organization via `ZOHO_ORGANIZATION_ID`.

- Multi-merchant SaaS deployments must run distinct connector instances per merchant organization or enforce tenant isolation at the process boundary.

- The AI agent cannot dynamically override the organization ID within a session.

## 3. Pull-Based Architecture — No Webhooks

- **No Push Notifications**: The connector operates through request-response MCP tool calls initiated by the AI agent.

- It does not host HTTP webhook listeners for Zoho Inventory status updates, order status changes, or low-stock alerts.

## 4. Not an ETL or Data Warehousing Pipeline

- **Context-Sized Retrieval**: The connector is optimized for targeted retrieval suitable for downstream LLM reasoning.

- Pagination, maximum-result limits, field projection, and response-size guards prevent unbounded retrieval.

- It is **not** designed for bulk exports, database backups, or historical ledger migrations involving hundreds of thousands of records.

## 5. No Semantic Vector Search

- Search tools (`search_items`, `search_sales_orders`, `search_contacts`) rely on Zoho-supported keyword/filter-based retrieval.

- The connector does not maintain a vector database, embedding index, or semantic search cache.

- Semantic interpretation of retrieved records remains the responsibility of the consuming AI agent.

## 6. No Direct Financial Transactions

- Although the connector can expose read-only financial fields such as `total`, `tax_total`, and `outstanding_receivable_amount`, it does not:
  - process financial transactions;
  - trigger payment gateway charges;
  - create payment transactions;
  - generate financial receipts.

- Integrations with payment systems such as Razorpay or Stripe are outside the connector's scope.

## 7. Upstream Rate Limit Ceiling

- Client-side rate limiting operates at 60 requests/minute to maintain safety headroom below Zoho's documented organization-level API quota.

- If other integrations consume the merchant's upstream quota, Zoho may still return HTTP 429 responses.

- The connector handles rate-limit responses using bounded retry/backoff behavior rather than attempting unlimited retries.

## 8. Live OAuth Validation Limitation

- The connector implements Zoho Inventory OAuth 2.0 configuration for the India data center and supports the required read-only credentials.

- During final validation, a live Self Client authorization-code exchange returned an HTTP 400 response from Zoho Accounts with a generic HTML error page.

- Because live merchant credentials could not be successfully validated, the final end-to-end MCP validation was performed using the connector's **explicit deterministic mock mode**.

- No production merchant data or credentials are included in the repository.

- This limitation does not affect the connector's read-only MCP interface, service-layer tests, resilience tests, security tests, or MCP protocol smoke test performed against the deterministic mock client.
