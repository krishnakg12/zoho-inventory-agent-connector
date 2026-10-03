"""
End-to-End Demonstration Script for Zoho Inventory MCP Connector.
Simulates realistic AI Agent conversations and tool invocations:
- Scenario 1: 'Find products with low available stock.'
- Scenario 2: 'Find recent sales orders for customer Acme.' (Multi-step Agent reasoning)
- Scenario 3: Context-window protection & pagination controls.
"""

import asyncio
import json
import sys

from zoho_connector.config import Settings
from zoho_connector.server import create_app


async def run_end_to_end_demo():
    print("=" * 75)
    print("  PRIVATE ZOHO INVENTORY CONNECTOR - AGENT MCP DEMO [MOCK MODE]  ")
    print("=" * 75)
    print("Architecture: Agent -> MCP Protocol -> Data Service -> Zoho Client\n")

    settings = Settings(app_mode="mock")
    server, client = create_app(settings=settings)

    try:
        # =====================================================================
        # SCENARIO 1: "Find products with low available stock"
        # =====================================================================
        print("-" * 75)
        print("SCENARIO 1: Inventory Health Analysis")
        print("User Request : 'Find products with low available stock.'")
        print("Agent Action : Invoking tool `list_items(status='lowstock')`")
        print("-" * 75)

        res1 = await server.call_tool("list_items", {"status": "lowstock", "per_page": 5})
        raw_payload1 = json.loads(res1.content[0].text)
        print("\n[MCP Response Payload]:")
        print(json.dumps(raw_payload1, indent=2))

        print("\n[Agent Synthesized Response]:")
        low_stock_items = raw_payload1.get("items", [])
        print(f"\"I found {len(low_stock_items)} items requiring attention based on current inventory levels:\n")
        for it in low_stock_items:
            stock = it["stock"]
            print(f"  • {it['name']} (SKU: {it['sku']}):")
            print(f"    - Available: {stock['available']} {stock.get('unit', 'units')}")
            print(f"    - Reorder Threshold: {stock.get('reorder_level')} units")
            print(f"    - Physical On Hand: {stock['on_hand']} units (Reserved: {stock['reserved']})")
            print(f"    - Selling Price: ${it['pricing']['selling_price']}\n")
        print("Recommendation: Restock orders should be placed immediately for these items.\"")

        # =====================================================================
        # SCENARIO 2: Multi-step Reasoning - "Find recent sales orders for customer Acme"
        # =====================================================================
        print("\n" + "=" * 75)
        print("SCENARIO 2: Multi-Step Customer & Sales Order Lookup")
        print("User Request : 'Find recent sales orders and balance for customer Acme.'")
        print("-" * 75)

        # Step 2a: Search contact
        print("\n[Step 1] Agent searches for contact matching 'Acme':")
        print("         Invoking `search_contacts(name='Acme')`...")
        res2a = await server.call_tool("search_contacts", {"name": "Acme"})
        data2a = json.loads(res2a.content[0].text)
        matched_contact = data2a["items"][0]
        contact_id = matched_contact["contact_id"]
        print(f"         Found Contact: {matched_contact['contact_name']} (ID: {contact_id})")

        # Step 2b: Get contact detail (with PII minimization)
        print("\n[Step 2] Agent retrieves account profile with PII protection:")
        print(f"         Invoking `get_contact(contact_id='{contact_id}', mask_pii=True)`...")
        res2b = await server.call_tool("get_contact", {"contact_id": contact_id, "mask_pii": True})
        contact_detail = json.loads(res2b.content[0].text)
        print(f"         Customer: {contact_detail['contact_name']}")
        print(f"         Masked Email: {contact_detail['email']}")
        print(f"         Outstanding Receivable: ${contact_detail['outstanding_receivable_amount']} {contact_detail['currency_code']}")

        # Step 2c: Search sales orders for this customer ID
        print(f"\n[Step 3] Agent searches sales orders placed by {contact_id}:")
        print(f"         Invoking `search_sales_orders(customer_id='{contact_id}')`...")
        res2c = await server.call_tool("search_sales_orders", {"customer_id": contact_id})
        orders_data = json.loads(res2c.content[0].text)
        orders = orders_data.get("items", [])
        print(f"         Retrieved {len(orders)} sales orders.")

        print("\n[Agent Synthesized Response]:")
        print(f"\"Here is the account summary for {contact_detail['contact_name']}:")
        print(f" • Outstanding Balance Due: ${contact_detail['outstanding_receivable_amount']} USD")
        print(f" • Recent Orders ({len(orders)} found):")
        for so in orders:
            print(f"   - Order {so['sales_order_number']}: Total ${so['total']} USD | Status: {so['status'].upper()} | Date: {so['date']}")
        print("All records have been retrieved directly from Zoho Inventory.\"")

        # =====================================================================
        # SCENARIO 3: Context-Window Protection & Pagination
        # =====================================================================
        print("\n" + "=" * 75)
        print("SCENARIO 3: Context-Window Protection & Explicit Pagination")
        print("User Request : 'Show me all items in inventory.'")
        print("Agent Action : Invoking `list_items(page=1, per_page=2)`")
        print("-" * 75)

        res3 = await server.call_tool("list_items", {"page": 1, "per_page": 2, "status": "all"})
        data3 = json.loads(res3.content[0].text)

        print("\n[Pagination & Truncation Metadata]:")
        print(f" • Page Retrieved : {data3['pagination']['page']} (Size: {data3['pagination']['per_page']})")
        print(f" • Total in Zoho  : {data3['pagination']['total_count']}")
        print(f" • Has More Pages : {data3['pagination']['has_more']}")
        print(f" • Truncation Info: {data3['truncation']['next_page_instruction']}")

        print("\n" + "=" * 75)
        print("  END-TO-END DEMO COMPLETED SUCCESSFULLY!  ")
        print("=" * 75)

    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(run_end_to_end_demo())
