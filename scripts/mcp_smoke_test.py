import asyncio
import os
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main():
    server_params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "zoho_connector.server"],
        env={
            **os.environ,
            "APP_MODE": "mock",
        },
    )

    print("Starting MCP server...")

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:

            print("Initializing MCP session...")
            await session.initialize()

            print("\n=== SERVER INITIALIZED ===")

            result = await session.list_tools()

            tools = result.tools

            print(f"\nDiscovered {len(tools)} tools:")

            for tool in tools:
                print(f"  - {tool.name}")

            expected = {
                "list_items",
                "get_item",
                "search_items",
                "list_sales_orders",
                "get_sales_order",
                "search_sales_orders",
                "list_contacts",
                "get_contact",
                "search_contacts",
            }

            discovered = {tool.name for tool in tools}

            missing = expected - discovered

            if missing:
                raise AssertionError(
                    f"Missing MCP tools: {sorted(missing)}"
                )

            print("\n✓ All 9 expected tools discovered")

            print("\nCalling list_items through MCP protocol...")

            response = await session.call_tool(
                "list_items",
                {
                    "page": 1,
                    "per_page": 2,
                },
            )

            if response.is_error:
                raise AssertionError(
                    f"MCP tool returned an error: {response}"
                )

            print("✓ list_items completed successfully")

            print("\nResponse:")
            for content in response.content:
                if hasattr(content, "text"):
                    print(content.text)

            print("\n================================")
            print("MCP PROTOCOL SMOKE TEST PASSED")
            print("================================")


if __name__ == "__main__":
    asyncio.run(main())