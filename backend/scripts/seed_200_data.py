"""
DealFlow360 — 200 Synthetic Data Seeder CLI Script
===================================================
CLI command to seed ~200 realistic, relationally connected synthetic records into 'bulk-data-lab'.

Usage:
    python scripts/seed_200_data.py
"""

import argparse
import asyncio
import os
import sys
import time

# Ensure backend directory is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.seed.seeder_200 import seed_200_data


async def main():
    print("=" * 80)
    print("DealFlow360 — 200 Synthetic Record Data Seeding System")
    print("=" * 80)
    print("Tenant Target : DealFlow360 Analytics Lab (slug: bulk-data-lab)")
    print("Target Count  : ~200 Connected Business Records")
    print("=" * 80)

    start_time = time.time()
    try:
        res = await seed_200_data()
        elapsed = time.time() - start_time

        print("\n" + "=" * 80)
        print("200-RECORD DATA SEEDING COMPLETED SUCCESSFULLY!")
        print("=" * 80)
        print(f"Execution Time          : {elapsed:.2f} seconds")
        print(f"Total Generated Records : {res.get('total_records', 0):,}")
        print("-" * 80)
        print(f"  Tenants               : 1")
        print(f"  Users (Staff/Admin)   : {res.get('users', 0)}")
        print(f"  Customers             : {res.get('customers', 0)}")
        print(f"  Customer Contacts     : {res.get('contacts', 0)}")
        print(f"  Products              : {res.get('products', 0)}")
        print(f"  Product Variants      : {res.get('product_variants', 0)}")
        print(f"  Warehouses            : {res.get('warehouses', 0)}")
        print(f"  Inventory Stocks      : {res.get('inventory_stocks', 0)}")
        print(f"  Pricing & Disc Rules  : {res.get('pricing_rules', 0) + res.get('discount_policies', 0)}")
        print(f"  Deals                 : {res.get('deals', 0)}")
        print(f"  Quotations            : {res.get('quotations', 0)}")
        print(f"  Quotation Line Items  : {res.get('quotation_items', 0)}")
        print(f"  Quotation Approvals   : {res.get('quotation_approvals', 0)}")
        print(f"  Fulfillment Shipments : {res.get('shipments', 0)}")
        print(f"  Backorders            : {res.get('backorders', 0)}")
        print(f"  Invoices              : {res.get('invoices', 0)}")
        print(f"  Invoice Items         : {res.get('invoice_items', 0)}")
        print(f"  Completed Payments    : {res.get('payments', 0)}")
        print(f"  Subscriptions         : {res.get('subscriptions', 0)}")
        print(f"  Billing Schedules     : {res.get('billing_schedules', 0)}")
        print(f"  Deal Health Snapshots : {res.get('deal_health_snapshots', 0)}")
        print(f"  Monitoring Events     : {res.get('monitoring_events', 0)}")
        print(f"  Nudges                : {res.get('nudges', 0)}")
        print(f"  CRM Activities        : {res.get('activities', 0)}")
        print(f"  Automation Executions : {res.get('automation_executions', 0)}")
        print("=" * 80)
        sys.exit(0)
    except Exception as exc:
        print(f"\n[ERROR] 200 data seeding failed: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
