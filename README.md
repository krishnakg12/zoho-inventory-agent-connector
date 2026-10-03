# Zoho Inventory MCP Connector

A production-grade, secure, read-only **Model Context Protocol (MCP)** connector for **Zoho Inventory**, engineered for AI agents to query merchant stock levels, sales orders, and customer records with zero risk of unauthenticated mutations, quota exhaustion, or prompt injection.

---

## 1. What the Project Does

The Zoho Inventory MCP Connector enables AI agents (such as Claude, ChatGPT, or custom LangGraph/CrewAI/LlamaIndex-free reasoning systems) to interact safely with a merchant's Zoho Inventory system.

Through 9 dedicated read-only MCP tools, an agent can:
- Query real-time inventory on-hand, reserved, and available stock levels.
- Identify products at or below low-stock reorder thresholds.
- Look up and search customer accounts and outstanding receivables.
- Retrieve sales orders, tracking fulfillment statuses and line item breakdowns.

---

## 2. Why It Exists

Standard SaaS APIs cannot be directly plugged into an AI agent without significant risk:
- **Prompt Injection**: Product descriptions or customer notes might contain malicious instructions designed to hijack LLM system prompts.
- **Context Window Bloat**: Raw Zoho JSON payloads contain hundreds of verbose internal fields that exhaust LLM context windows and skyrocket inference costs.
- **Rate-Limit Lockouts**: Unchecked LLM loops can exhaust a merchant's API quota (100 req/min in Zoho), causing company-wide service disruptions.
- **Accidental Mutations**: A poorly constrained agent might unintentionally modify stock, void orders, or alter prices.
- **Credential Leakage**: Unsanitized logs or raw tool error traces risk leaking OAuth bearer tokens.

This connector acts as a protective boundary: normalizing data, enforcing read-only security, bounding pagination, rate-limiting outbound calls, and isolating merchant tenants.

---

## 3. Architecture

```
USER / MERCHANT
        |
        | Natural language
        v
AI AGENT (Claude Desktop, Cline, Cursor, Custom Agent)
        |
        | Model Context Protocol (MCP JSON-RPC over STDIO)
        v
MCP SERVER (zoho-inventory-connector)
        |
        +-- 9 Read-Only MCP Tools (Pydantic validated)
        |
DATA SERVICE LAYER
        |
        +-- Field Projection & Normalization
        +-- PII Minimization & Masking
        +-- Context-Window Byte Budgeting & Truncation Guards
        |
        v
ZOHO CLIENT ADAPTER
        |
        +----------------------------+
        |                            |
        v                            v
[APP_MODE=live]              [APP_MODE=mock]
ZohoInventoryClient          MockZohoClient
  • OAuth Token Manager        • Deterministic offline fixtures
  • Token Bucket Rate Limiter  • Zero network dependencies
  • Concurrency Semaphore      • Realistic merchant scenarios
  • Exponential Retry Engine
        |
        | HTTPS / JSON (Zoho-oauthtoken)
        v
ZOHO INVENTORY REST API (v1)
```

See [`ARCHITECTURE.md`](file:///c:/Users/krish/OneDrive/razorpay_zoho_inventory_connector/ARCHITECTURE.md) for full technical design details.

---

## 4. Requirements

- **Python**: 3.12 or newer
- **Virtual Environment & Package Manager**: `uv` or standard Python `venv` + `pip`
- **Zoho Inventory Account** (only required for `APP_MODE=live`; mock mode works completely offline)

---

## 5. Setup Instructions

### 5.1 Clone & Setup Environment

```powershell
# Clone the repository and navigate into it
cd razorpay_zoho_inventory_connector

# Create a virtual environment using uv
uv venv .venv

# Activate the virtual environment
.venv\Scripts\activate   # Windows PowerShell
# source .venv/bin/activate # Linux/macOS

# Install dependencies and package in editable mode
uv pip install -e .
```

---

## 6. OAuth 2.0 Configuration (Live Mode Only)

If deploying against a live Zoho Inventory organization:

1. Log into the [Zoho Developer Console](https://api-console.zoho.com/).
2. Create a **Server-based Application**.
3. Note your **Client ID** and **Client Secret**.
4. Generate a permanent **Refresh Token** with the minimum read scopes:
   - `ZohoInventory.items.READ`
   - `ZohoInventory.salesorders.READ`
   - `ZohoInventory.contacts.READ`
5. Retrieve your numeric **Organization ID** from Zoho Inventory (found under *Settings > Organization Profile*).

---

## 7. Environment Variables

Create your `.env` file from `.env.example`:

```powershell
cp .env.example .env
```

| Variable | Required in Live? | Default | Description |
| :--- | :--- | :--- | :--- |
| `APP_MODE` | No | `mock` | `mock` (deterministic offline) or `live` (Zoho API) |
| `ZOHO_ORGANIZATION_ID` | Yes | - | Numeric merchant organization ID in Zoho |
| `ZOHO_CLIENT_ID` | Yes | - | Zoho OAuth Client ID |
| `ZOHO_CLIENT_SECRET` | Yes | - | Zoho OAuth Client Secret |
| `ZOHO_REFRESH_TOKEN` | Yes | - | Zoho permanent Refresh Token |
| `ZOHO_BASE_URL` | No | `https://www.zohoapis.com/inventory/v1` | Zoho Inventory API base URL (region dependent) |
| `ZOHO_ACCOUNTS_URL` | No | Auto-derived | Zoho Accounts endpoint for token refresh |
| `RATE_LIMIT_REQUESTS_PER_MINUTE` | No | `60` | Client rate limit (safety headroom below 100/min) |
| `MAX_CONCURRENT_REQUESTS` | No | `5` | Semaphore limit for concurrent outbound HTTP requests |
| `MAX_RETRIES` | No | `3` | Maximum retry attempts for transient server errors |
| `REQUEST_TIMEOUT_SECONDS` | No | `15.0` | HTTP client timeout in seconds |
| `DEFAULT_PAGE_SIZE` | No | `10` | Default record count per page |
| `MAX_PAGE_SIZE` | No | `50` | Hard cap on items returned per page |
| `MAX_RESPONSE_BYTES` | No | `65536` | Response byte budget before explicit truncation |
| `LOG_LEVEL` | No | `INFO` | Console log level (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |
| `LOG_JSON` | No | `False` | Enable structured JSON formatting for logs |

---

## 8. Running Locally

### Health Check Probe
Run the built-in diagnostic script to test your environment and adapter health:

```powershell
.venv\Scripts\python scripts/health_check.py
```

### Interactive End-to-End Demo
Simulate an AI agent interacting with the MCP server:

```powershell
.venv\Scripts\python scripts/run_demo.py
```

---

## 9. Running Tests

The test suite contains 70 automated tests covering unit logic, integration pipelines, security controls, pagination bounds, rate limiting, and MCP tools:

```powershell
# Run the complete test suite
.venv\Scripts\pytest -v

# Run specific test modules
.venv\Scripts\pytest tests/unit/test_auth.py
.venv\Scripts\pytest tests/unit/test_security.py
.venv\Scripts\pytest tests/mcp/test_mcp_tools.py
```

---

## 10. Starting the MCP Server

Start the MCP server using standard I/O (JSON-RPC over STDIO):

```powershell
# Using the installed script entrypoint
.venv\Scripts\zoho-mcp-server

# Or using python module execution
.venv\Scripts\python -m zoho_connector.server
```

---

## 11. Connecting an MCP Client

### Claude Desktop Configuration
Add the connector to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "zoho-inventory": {
      "command": "C:\\Users\\krish\\OneDrive\\razorpay_zoho_inventory_connector\\.venv\\Scripts\\python.exe",
      "args": [
        "-m",
        "zoho_connector.server"
      ],
      "env": {
        "APP_MODE": "mock"
      }
    }
  }
}
```

*(For live mode, change `APP_MODE` to `live` and supply your `ZOHO_*` credentials in the `env` block or in a local `.env` file.)*

---

## 12. Implemented MCP Tools

| Module | Tool Name | Description | Key Parameters |
| :--- | :--- | :--- | :--- |
| **Items** | `list_items` | List items with stock metrics and prices | `page`, `per_page`, `status`, `sort_by` |
| **Items** | `get_item` | Detailed item record with categories & units | `item_id` |
| **Items** | `search_items` | Search products by name, SKU, or keyword | `query`, `page`, `per_page`, `filter_by` |
| **Orders** | `list_sales_orders` | List sales orders with status and totals | `page`, `per_page`, `status`, `customer_id` |
| **Orders** | `get_sales_order` | Sales order details including line items | `sales_order_id` |
| **Orders** | `search_sales_orders` | Search orders by number, customer, keyword | `query`, `customer_id`, `order_number` |
| **Contacts**| `list_contacts` | List customers or vendors with balances | `page`, `per_page`, `contact_type`, `status` |
| **Contacts**| `get_contact` | Contact profile with optional PII masking | `contact_id`, `mask_pii` |
| **Contacts**| `search_contacts` | Search contacts by name, company, or email | `name`, `company`, `email`, `page`, `per_page` |

See [`examples/sample_queries.md`](file:///c:/Users/krish/OneDrive/razorpay_zoho_inventory_connector/examples/sample_queries.md) for concrete examples.

---

## 13. Security Model Highlights

- **Strict Read-Only**: Zero write, update, or deletion tools exist.
- **Tenant Isolation**: The AI agent cannot manipulate `organization_id`; requests are permanently locked to the server's configured merchant organization.
- **Prompt Injection Defense**: All responses attach an explicit untrusted content disclaimer notice instructing the agent to treat data strictly as data.
- **Secret Redaction**: Logging filters automatically sanitize tokens, client secrets, and bearer headers before writing to `sys.stderr`.
- **Mock Isolation**: Failures in live mode never fall back to mock data, preventing hallucinated merchant actions.

See [`SECURITY.md`](file:///c:/Users/krish/OneDrive/razorpay_zoho_inventory_connector/SECURITY.md) for full threat modeling.

---

## 14. Limitations

- Does not support write-back operations (e.g., creating sales orders or updating stock counts).
- Bound to a single merchant organization per running process.
- Pull-based queries only; does not receive webhook push events from Zoho.

See [`LIMITATIONS.md`](file:///c:/Users/krish/OneDrive/razorpay_zoho_inventory_connector/LIMITATIONS.md) for complete details.

---

## 15. Future Production Improvements

1. **Redis Token Cache**: Share OAuth access tokens across multi-process cluster deployments.
2. **Inbound Webhook Receiver**: Stream real-time low-stock alerts to proactive background agents.
3. **Multi-Tenant Gateway**: Dynamically map client API keys to distinct merchant Zoho organizations.
4. **OpenTelemetry Tracing**: Export distributed traces and metrics to Datadog or Prometheus.
