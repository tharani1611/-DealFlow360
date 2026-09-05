"""
DealFlow360 — Reset Bulk Data CLI Script
=========================================
Safely purges records belonging STRICTLY to the bulk analytics tenants:
- 'bulk-data-lab'
- 'bulk-isolation-lab'

Does NOT delete 'demo-enterprise', 'acme-global', or any other tenant data.
Requires explicit '--confirm' flag for execution safety.

Usage:
    python scripts/reset_bulk_data.py --confirm
"""

import argparse
import asyncio
import os
import sys

# Ensure backend directory is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.seed.bulk_seeder import reset_bulk_data


async def main():
    parser = argparse.ArgumentParser(description="DealFlow360 Reset Bulk Data")
    parser.add_argument(
        "--confirm",
        action="store_true",
        help="Required safety flag to confirm purge of bulk-data-lab and bulk-isolation-lab data"
    )
    args = parser.parse_args()

    print("=" * 70)
    print("DealFlow360 — Reset Bulk Analytics Dataset")
    print("=" * 70)

    if not args.confirm:
        print("\n[SAFETY ABORT] The '--confirm' flag is required to reset bulk data.")
        print("Example: python scripts/reset_bulk_data.py --confirm")
        print("=" * 70)
        sys.exit(1)

    try:
        print("Purging bulk dataset organizations ('bulk-data-lab', 'bulk-isolation-lab')...")
        res = await reset_bulk_data()
        print("\nReset Completed Successfully!")
        print(f"Purged Organizations: {res.get('purged_organizations', 0)}")
        print("=" * 70)
        sys.exit(0)
    except Exception as exc:
        print(f"\n[ERROR] Bulk data reset failed: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
