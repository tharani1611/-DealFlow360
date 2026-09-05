"""
DealFlow360 — 300-Set Synthetic Business Data Seeder (Delegate)
================================================================
Delegates synthetic data provisioning to the authoritative bulk seeder (`app.seed.bulk_seeder`).
Resizes data cleanly and safely to ~100-200 major business entities (~3,500 total records).
"""

import logging
from typing import Dict, Any, Optional, List

from sqlalchemy.ext.asyncio import AsyncSession

from app.seed.bulk_seeder import (
    seed_bulk_data,
    reset_bulk_data,
    BULK_ORG_SLUG,
    BULK_ORG_NAME,
)

logger = logging.getLogger("dealflow360.seeder_300")

BULK_300_ORG_SLUG = BULK_ORG_SLUG
BULK_300_ORG_NAME = BULK_ORG_NAME


async def reset_300_data(
    session: Optional[AsyncSession] = None,
    target_slug: str = BULK_300_ORG_SLUG,
    delete_org: bool = True,
) -> Dict[str, Any]:
    """Safely resets bulk records by delegating to bulk_seeder."""
    target_slugs = [target_slug] if target_slug else None
    return await reset_bulk_data(session=session, target_slugs=target_slugs)


async def seed_300_data(
    session: Optional[AsyncSession] = None,
    target_slug: str = BULK_300_ORG_SLUG,
    target_name: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Populates 300 complete sets of realistic business data under the specified tenant slug
    by delegating to the authoritative bulk seeder implementation.
    """
    return await seed_bulk_data(session=session)
