"""
DealFlow360 — Demo Data Seeder Script (Phase 78)
================================================
CLI entrypoint to seed idempotent demo data and showcase scenarios.
Usage:
    python scripts/seed_demo_data.py
"""

import asyncio
import sys
import os

# Ensure backend directory is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.seed.demo_seeder import seed_demo_data


async def main():
    print("=" * 70)
    print("DealFlow360 — Provisioning Demo Data Environment (Phase 78)")
    print("=" * 70)
    try:
        res = await seed_demo_data()
        print("\nDemo Data Seeding Completed Successfully!")
        print(f"Organization  : {res.get('demo_organization')}")
        print(f"Slug          : {res.get('demo_slug')}")
        print(f"Users Created : {res.get('users_created')}")
        print(f"Customers     : {res.get('customers_created')}")
        print(f"Products      : {res.get('products_created')}")
        print(f"Warehouses    : {res.get('warehouses_created')}")
        print(f"Scenarios Run : {res.get('scenarios_executed')}")
        print("=" * 70)
        sys.exit(0)
    except Exception as exc:
        print(f"\n[ERROR] Demo seeding failed: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
