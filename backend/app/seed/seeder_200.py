"""
DealFlow360 — 200-Record Realistic Synthetic Data Seeder (Delegate)
===================================================================
Delegates synthetic data provisioning to the authoritative bulk seeder (`app.seed.bulk_seeder`).
Resizes data cleanly and safely to ~100-200 major business entities (~3,500 total records).
"""

import logging
from typing import Dict, Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.seed.bulk_seeder import (
    seed_bulk_data,
    reset_bulk_data,
    BULK_ORG_SLUG,
    BULK_ORG_NAME,
)

logger = logging.getLogger("dealflow360.seeder_200")

BULK_200_ORG_SLUG = BULK_ORG_SLUG
BULK_200_ORG_NAME = BULK_ORG_NAME


async def reset_200_data(session: Optional[AsyncSession] = None) -> Dict[str, Any]:
    """Safely resets bulk records by delegating to bulk_seeder."""
    return await reset_bulk_data(session=session)


async def seed_200_data(session: Optional[AsyncSession] = None) -> Dict[str, Any]:
    """
    Populates realistic, relationally connected synthetic records under the 'bulk-data-lab' tenant
    by delegating to the authoritative bulk seeder implementation.
    """
    return await seed_bulk_data(session=session)
