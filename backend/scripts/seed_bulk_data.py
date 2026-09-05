"""
DealFlow360 — Bulk Data Seeder CLI Script
==========================================
CLI command to seed a realistic, medium-volume bulk dataset (~3,500 records) into 'bulk-data-lab'.

Usage:
    python scripts/seed_bulk_data.py
"""

import argparse
import asyncio
import os
import sys
import time

# Ensure backend directory is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.seed.bulk_seeder import seed_bulk_data


async def main():
    parser = argparse.ArgumentParser(description="DealFlow360 Bulk Data Seeder")
    parser.add_argument("--count", type=int, default=3500, help="Target record count threshold")
    args = parser.parse_args()

    print("=" * 80)
    print("DealFlow360 — Resized Bulk Data Seeding System (~3,500 Records)")
    print("=" * 80)
    print(f"Target Major Entity Counts    : 120 Customers, 120 Products, 120 Deals, 120 Quotations")
    print("Tenant Target                 : DealFlow360 Analytics Lab (slug: bulk-data-lab)")
    print("Isolation Tenant              : DealFlow360 Isolation Testing Lab (slug: bulk-isolation-lab)")
    print("=" * 80)

    start_time = time.time()
    try:
        res = await seed_bulk_data()
        elapsed = time.time() - start_time

        print("\n" + "=" * 80)
        print("BULK DATA SEEDING COMPLETED SUCCESSFULLY!")
        print("=" * 80)
        print(f"Execution Time                : {elapsed:.2f} seconds")
        print(f"Total Generated Records       : {res.get('total_records', 0):,}")
        print("-" * 80)
        print(f"  Tenants                     : {res.get('tenants', 0)}")
        print(f"  Users (Staff & Admin)       : {res.get('users', 0)}")
        print(f"  Portal Users                : {res.get('portal_users', 0)}")
        print(f"  Customers                   : {res.get('customers', 0)}")
        print(f"  Customer Contacts           : {res.get('contacts', 0)}")
        print(f"  Products                    : {res.get('products', 0)}")
        print(f"  Product Variants            : {res.get('product_variants', 0)}")
        print(f"  Warehouses                  : {res.get('warehouses', 0)}")
        print(f"  Inventory Stock Locations   : {res.get('inventory_stocks', 0)}")
        print(f"  Inventory Movements         : {res.get('inventory_movements', 0)}")
        print(f"  Pricing Rules               : {res.get('pricing_rules', 0)}")
        print(f"  Discount Governance Rules   : {res.get('discount_policies', 0)}")
        print(f"  Recommendation Rules        : {res.get('recommendation_rules', 0)}")
        print(f"  Approval Rules              : {res.get('approval_rules', 0)}")
        print(f"  Deals                       : {res.get('deals', 0)}")
        print(f"  Quotations                  : {res.get('quotations', 0)}")
        print(f"  Quotation Line Items        : {res.get('quotation_items', 0)}")
        print(f"  Quotation State Histories   : {res.get('quotation_state_histories', 0)}")
        print(f"  Quotation Approvals         : {res.get('quotation_approvals', 0)}")
        print(f"  Approval Audit Logs         : {res.get('approval_audit_logs', 0)}")
        print(f"  Quotation Line Comments     : {res.get('quotation_comments', 0)}")
        print(f"  Quotation Change Requests   : {res.get('quotation_changes', 0)}")
        print(f"  Quotation Versions          : {res.get('quotation_versions', 0)}")
        print(f"  Warehouse Allocations       : {res.get('warehouse_allocations', 0)}")
        print(f"  Billing Classifications     : {res.get('billing_classifications', 0)}")
        print(f"  Inventory Reservations      : {res.get('inventory_reservations', 0)}")
        print(f"  Shipments                   : {res.get('shipments', 0)}")
        print(f"  Shipment Lines              : {res.get('shipment_lines', 0)}")
        print(f"  Backorders                  : {res.get('backorders', 0)}")
        print(f"  Delivery SLA Promises       : {res.get('delivery_promises', 0)}")
        print(f"  Invoices                    : {res.get('invoices', 0)}")
        print(f"  Invoice Line Items          : {res.get('invoice_items', 0)}")
        print(f"  Completed Payments          : {res.get('payments', 0)}")
        print(f"  Credit Notes                : {res.get('credit_notes', 0)}")
        print(f"  Credit Note Items           : {res.get('credit_note_items', 0)}")
        print(f"  Payment Cash Refunds        : {res.get('payment_refunds', 0)}")
        print(f"  Subscriptions               : {res.get('subscriptions', 0)}")
        print(f"  Billing Schedules           : {res.get('billing_schedules', 0)}")
        print(f"  Subscription Cancellations  : {res.get('subscription_cancellations', 0)}")
        print(f"  Deal Health Snapshots       : {res.get('deal_health_snapshots', 0)}")
        print(f"  Anomaly Monitoring Events   : {res.get('monitoring_events', 0)}")
        print(f"  Nudges                      : {res.get('nudges', 0)}")
        print(f"  Nudge Histories             : {res.get('nudge_histories', 0)}")
        print(f"  CRM Activities              : {res.get('activities', 0)}")
        print(f"  Automation Rules            : {res.get('automation_rules', 0)}")
        print(f"  Automation Executions       : {res.get('automation_executions', 0)}")
        print(f"  Automation Execution Actions: {res.get('automation_execution_actions', 0)}")
        print("=" * 80)
        sys.exit(0)
    except Exception as exc:
        print(f"\n[ERROR] Bulk data seeding failed: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
