"""
DealFlow360 — 300 Synthetic Data Sets Seeder CLI Script
=========================================================
CLI command to seed 300 complete sets of realistic, relationally connected synthetic business records (~3,500+ records) into 'bulk-data-lab'.

Usage:
    python scripts/seed_300_data.py
"""

import asyncio
import os
import sys
import time

# Ensure backend directory is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.seed.seeder_300 import seed_300_data


async def main():
    target_slugs = sys.argv[1:] if len(sys.argv) > 1 else ["bulk-data-lab", "odo0"]
    
    print("=" * 80)
    print("DealFlow360 — 300 Synthetic Data Sets Seeding System")
    print("=" * 80)
    print(f"Tenant Targets: {', '.join(target_slugs)}")
    print("Target Count  : 300 Complete Sets per tenant (~3,500+ Connected Business Records)")
    print("=" * 80)

    start_time = time.time()
    try:
        for slug in target_slugs:
            print(f"\n---> Seeding 300 Data Sets for tenant slug '{slug}'...")
            res = await seed_300_data(target_slug=slug)
            print(f"[{slug}] Seeding Completed! Total Records: {res.get('total_records', 0):,}")
            print(f"[{slug}] Customers: {res.get('customers', 0)} | Deals: {res.get('deals', 0)} | Quotes: {res.get('quotations', 0)} | Invoices: {res.get('invoices', 0)}")

        elapsed = time.time() - start_time
        print("\n" + "=" * 80)
        print("ALL 300 SETS DATA SEEDING COMPLETED SUCCESSFULLY!")
        print(f"Total Execution Time: {elapsed:.2f} seconds")
        print("=" * 80)
        sys.exit(0)
    except Exception as exc:
        print(f"\n[ERROR] 300 data sets seeding failed: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
