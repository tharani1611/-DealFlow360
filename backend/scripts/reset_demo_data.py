"""
DealFlow360 — Demo Data Reset Script (Phase 78)
===============================================
CLI entrypoint to safely wipe and reset demo data.
Usage:
    python scripts/reset_demo_data.py
"""

import asyncio
import sys
import os

# Ensure backend directory is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.seed.demo_seeder import reset_demo_data


async def main():
    print("=" * 70)
    print("DealFlow360 — Resetting Demo Data Environment (Phase 78)")
    print("=" * 70)
    try:
        res = await reset_demo_data()
        print("\nDemo Data Reset Completed Successfully!")
        print(f"Status        : {res.get('status')}")
        print(f"Purged Tenancy: {res.get('purged_organizations')}")
        print("=" * 70)
        sys.exit(0)
    except Exception as exc:
        print(f"\n[ERROR] Demo reset failed: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
