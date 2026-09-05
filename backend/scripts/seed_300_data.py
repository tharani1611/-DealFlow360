"""
DealFlow360 — 300 Synthetic Data Sets Seeder CLI Script
=========================================================
CLI command to seed complete sets of realistic synthetic business records into 'bulk-data-lab'.

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
    target_slugs = sys.argv[1:] if len(sys.argv) > 1 else ["bulk-data-lab"]
    
    print("=" * 80)
    print("DealFlow360 — Resized Bulk Data Seeding System (300-Set Delegate)")
    print("=" * 80)
    print(f"Tenant Targets: {', '.join(target_slugs)}")
    print("Target Count  : ~100–200 Major Entities (~3,500 Total Records per run)")
    print("=" * 80)

    start_time = time.time()
    try:
        for slug in target_slugs:
            print(f"\n---> Seeding Bulk Dataset for tenant slug '{slug}'...")
            res = await seed_300_data(target_slug=slug)
            print(f"[{slug}] Seeding Completed! Total Records: {res.get('total_records', 0):,}")
            print(f"[{slug}] Customers: {res.get('customers', 0)} | Deals: {res.get('deals', 0)} | Quotes: {res.get('quotations', 0)} | Invoices: {res.get('invoices', 0)}")

        elapsed = time.time() - start_time
        print("\n" + "=" * 80)
        print("DATA SEEDING COMPLETED SUCCESSFULLY!")
        print(f"Total Execution Time: {elapsed:.2f} seconds")
        print("=" * 80)
        sys.exit(0)
    except Exception as exc:
        print(f"\n[ERROR] Data seeding failed: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
