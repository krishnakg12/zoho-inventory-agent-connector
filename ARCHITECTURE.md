# Architecture Design: Zoho Inventory MCP Connector

## 1. System Overview

The **Zoho Inventory MCP Connector** is a secure, read-only integration layer that bridges AI reasoning agents and Zoho Inventory through the open **Model Context Protocol (MCP)** standard.

```
USER / MERCHANT
        |
        | Natural language
        v
AI AGENT (Claude, GPT, Open-Source Agent)
        |
        | Model Context Protocol (MCP JSON-RPC over STDIO)
        v
MCP SERVER (zoho-inventory-connector)
        |
        +-- mcp/tools.py (Input validation, exception wrapping, prompt defense)
        |
DATA SERVICE LAYER (src/zoho_connector/services/)
        |
        +-- Field projection & normalization
        +-- PII minimization
        +-- Context-window protection & truncation bounds
        |
        v
ZOHO CLIENT ADAPTER (src/zoho_connector/clients/)
        |
        +----------------------------+
        |                            |
        v                            v
[APP_MODE=live]              [APP_MODE=mock]
ZohoInventoryClient          MockZohoClient
  - Token Manager (OAuth 2)    - Deterministic offline fixtures
  - Rate Limiter (Token bucket)- No network dependencies
  - Concurrency Limiter (Sem)  - Zero risk of quota exhaustion
  - Retry Engine (Jitter)
        |
        | HTTPS / JSON (Zoho-oauthtoken)
        v
ZOHO INVENTORY API (REST v1)
```

---

## 2. Core Components

### 2.1 MCP Protocol Layer (`src/zoho_connector/mcp/`)
- Implements MCP 2.x standard server (`MCPServer`).
- Exposes 9 strictly read-only tools:
  - Items: `list_items`, `get_item`, `search_items`
  - Sales Orders: `list_sales_orders`, `get_sales_order`, `search_sales_orders`
  - Contacts: `list_contacts`, `get_contact`, `search_contacts`
- Applies `@safe_tool_handler` decorator:
  - Traps domain exceptions (`ZohoConnectorError`) and serializes them into structured, actionable JSON payloads.
  - Automatically tags all payloads with an untrusted content disclaimer to defend against prompt injection.

### 2.2 Data Service Layer (`src/zoho_connector/services/`)
- Positioned between the protocol tools and the raw HTTP client adapters.
- Normalizes incoming tool parameters (e.g. converting human-readable status strings into Zoho's internal `filter_by` tokens).
- Projects verbose Zoho JSON responses into lightweight Pydantic domain models:
  - Eliminates extraneous internal fields (e.g., custom layout flags, internal IDs, raw template IDs).
  - Normalizes stock quantities into `on_hand`, `reserved`, and `available`.
- Enforces context-window budget protection: if serialized records exceed `max_response_bytes`, records are safely trimmed and accompanied by explicit pagination/truncation instructions instead of silently truncating data.

### 2.3 Client Layer (`src/zoho_connector/clients/`)
- Unified under the runtime-checkable `ZohoClientProtocol`.
- **`ZohoInventoryClient`**:
  - Full-featured asynchronous HTTP transport using `httpx.AsyncClient` with connection pooling (`max_keepalive_connections=5`, `max_connections=20`).
  - Automatically manages OAuth 2.0 access token injection.
  - Guarantees tenant isolation: injects the merchant `organization_id` into every outbound query without allowing model override.
- **`MockZohoClient`**:
  - Deterministic in-memory client populated with realistic merchant fixtures.
  - Completely offline; provides identical pagination, filtering, search, and error semantics.
  - **Strict Isolation**: Active only when `APP_MODE=mock`. If `APP_MODE=live`, API failures NEVER fall back to mock data.

---

## 3. Cross-Cutting Engineering Controls

### 3.1 Authentication & Token Lifecycle (`src/zoho_connector/auth/oauth.py`)
- Employs an `OAuthTokenManager` using Zoho's refresh token grant.
- **Mutual Exclusion & Stampede Protection**: Uses `asyncio.Lock()` with double-checked locking. If multiple concurrent agent tool requests detect an expired token, exactly one network call refreshes the token, while all other requests wait and reuse the newly cached token.
- **Expiry Buffering**: Preemptively refreshes the token 300 seconds (5 minutes) before expiration to avoid edge-case mid-flight 401s.
- **Token Invalidation**: Automatically clears cached tokens when receiving an upstream HTTP 401.

### 3.2 Rate Limiting & Safety Headroom (`src/zoho_connector/resilience/rate_limiter.py`)
- Zoho Inventory enforces a hard limit of 100 requests per minute per organization.
- Connector implements an asynchronous **Token Bucket** algorithm calibrated to 60 requests/minute by default (customizable via `RATE_LIMIT_REQUESTS_PER_MINUTE`).
- By operating client-side throttling at 60% of upstream quota, the connector guarantees a 40% safety headroom for other merchant applications sharing the same organization.

### 3.3 Concurrency Control (`src/zoho_connector/resilience/concurrency.py`)
- Restricts total concurrent outbound HTTP requests using an `asyncio.Semaphore` (default: 5 concurrent requests).
- Prevents socket exhaustion, DNS stampedes, and upstream rate spikes.

### 3.4 Bounded Retries with Exponential Backoff & Jitter (`src/zoho_connector/resilience/retry.py`)
- Distinguishes strictly between transient and non-retryable failures:
  - **Retryable Candidates**: HTTP 429 (Too Many Requests), HTTP 500, 502, 503, 504, connection timeouts, and network drops.
  - **Non-Retryable Candidates**: HTTP 400, 401, 403, 404, input validation errors, and domain business rejections.
- Uses exponential backoff with full randomized jitter:
  $$\text{delay} = \text{random.uniform}(0.5 \times \text{backoff}, \text{backoff})$$
- Respects upstream `Retry-After` headers (numeric seconds or HTTP-date).
- Strictly bounded by `max_retries` (default: 3); never retries indefinitely.

### 3.5 Bounded Pagination & Context Window Protection (`src/zoho_connector/services/base.py`)
- Every list operation requires explicit 1-indexed pagination (`page`) and bounded limit (`per_page`).
- Hard upper bound: `max_page_size` (default: 50 records).
- Dual protection:
  1. Record count bounding (`per_page`).
  2. Byte-budget bounding (`max_response_bytes`, default: 64 KB).
  If a merchant payload exceeds the byte budget, records are trimmed with explicit `TruncationMetadata` instructing the agent how to page for remaining records.

### 3.6 Error Normalization (`src/zoho_connector/errors.py`)
- All low-level exceptions (HTTP status errors, connection timeouts, Zoho business code payloads) are translated into normalized domain exceptions:
  - `AuthenticationError` (code: `AUTHENTICATION_ERROR`)
  - `AuthorizationError` (code: `AUTHORIZATION_ERROR`)
  - `NotFoundError` (code: `NOT_FOUND`)
  - `RateLimitError` (code: `RATE_LIMIT_EXCEEDED`)
  - `ValidationError` (code: `VALIDATION_ERROR`)
  - `UpstreamUnavailableError` (code: `UPSTREAM_UNAVAILABLE`)
  - `UpstreamTimeoutError` (code: `UPSTREAM_TIMEOUT`)
  - `InternalConnectorError` (code: `INTERNAL_CONNECTOR_ERROR`)
- Responses contain error codes, human-readable explanations, and retryability flags. Raw internal tracebacks, authorization headers, and secrets are strictly excluded.

---

## 4. Architectural Trade-offs & Decisions

| Decision | Alternative Considered | Rationale |
| :--- | :--- | :--- |
| **Pure Python Async I/O (httpx, asyncio)** | Sync requests with thread pools | Async handles concurrent agent requests and rate-limit waits with minimal memory overhead and zero thread locking issues. |
| **Client-Side Token Bucket** | Reactive 429 backoff only | Reactive-only backoff risks temporary IP bans from Zoho (up to 30 minutes). Proactive throttling maintains a safety buffer. |
| **Separated Mock Adapter (`APP_MODE`)** | Silent fallback to mock on API failure | Silent fallback causes agents to present fabricated merchant data as real facts, violating data integrity. Explicit modes guarantee determinism. |
| **Field Projection in Service Layer** | Passing raw Zoho JSON directly | Raw Zoho responses contain hundreds of internal fields, consuming model tokens and risking prompt injection from unverified metadata. |
| **No External Database / Cache** | Redis / PostgreSQL | Connector is designed as a stateless, lightweight sidecar process that attaches to AI agents without infrastructure burden. |
