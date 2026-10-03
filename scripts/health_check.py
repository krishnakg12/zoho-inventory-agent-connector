"""
Health check diagnostic script for Zoho Inventory MCP Connector.
Verifies configuration validity, client adapter readiness, and connectivity.
Exits 0 if healthy, 1 if unhealthy.
"""

import asyncio
import sys
from zoho_connector.config import get_settings
from zoho_connector.server import create_app


async def run_health_check() -> int:
    sys.stdout.write("==================================================\n")
    sys.stdout.write("  ZOHO INVENTORY MCP CONNECTOR - HEALTH CHECK     \n")
    sys.stdout.write("==================================================\n\n")

    settings = get_settings()
    sys.stdout.write(f"[1/3] Checking Configuration...\n")
    sys.stdout.write(f"      - Operating Mode      : {settings.app_mode.upper()}\n")
    sys.stdout.write(f"      - Zoho Base URL       : {settings.zoho_base_url}\n")
    sys.stdout.write(f"      - Accounts URL        : {settings.zoho_accounts_url}\n")
    sys.stdout.write(f"      - Rate Limit Quota    : {settings.rate_limit_requests_per_minute} req/min\n")
    sys.stdout.write(f"      - Max Concurrency     : {settings.max_concurrent_requests}\n")
    sys.stdout.write(f"      - Page Size Bounds    : default={settings.default_page_size}, max={settings.max_page_size}\n")
    sys.stdout.write("      Status: CONFIG_VALID\n\n")

    sys.stdout.write(f"[2/3] Initializing Server & Adapter...\n")
    try:
        server, client = create_app(settings=settings)
        tools = await server.list_tools()
        sys.stdout.write(f"      - Server Name         : {server.name}\n")
        sys.stdout.write(f"      - Registered Tools    : {len(tools)} tools\n")
        for tool in tools:
            sys.stdout.write(f"        * {tool.name}\n")
        sys.stdout.write("      Status: ADAPTER_READY\n\n")
    except Exception as exc:
        sys.stderr.write(f"      Error initializing adapter: {exc}\n")
        return 1

    sys.stdout.write(f"[3/3] Testing Basic Read Operation (list_items)...\n")
    try:
        sample_res = await client.list_items({"page": 1, "per_page": 1})
        page_ctx = sample_res.get("page_context", {})
        sys.stdout.write(f"      - Upstream/Mock Call  : SUCCESS\n")
        sys.stdout.write(f"      - Records Available   : {page_ctx.get('total', 'unknown')}\n")
        sys.stdout.write("      Status: DATA_FLOW_HEALTHY\n\n")
    except Exception as exc:
        sys.stderr.write(f"      Error executing health probe: {exc}\n")
        return 1
    finally:
        await client.close()

    sys.stdout.write("==================================================\n")
    sys.stdout.write("  RESULT: ALL HEALTH CHECKS PASSED (HEALTHY)      \n")
    sys.stdout.write("==================================================\n")
    return 0


def main():
    code = asyncio.run(run_health_check())
    sys.exit(code)


if __name__ == "__main__":
    main()
