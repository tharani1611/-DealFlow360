import uuid
from datetime import datetime, timezone
from typing import Tuple
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.portal_user import PortalUser
from app.schemas.portal import PortalLoginRequest
from app.core.security import verify_password, create_access_token
from app.core.exceptions import UnauthorizedException


async def authenticate_portal_user(
    db: AsyncSession,
    request: PortalLoginRequest
) -> Tuple[PortalUser, str]:
    """Authenticates a customer portal user using email and password across portal users."""
    email = request.email.strip().lower()

    stmt = (
        select(PortalUser)
        .options(
            selectinload(PortalUser.customer),
            selectinload(PortalUser.organization)
        )
        .where(PortalUser.email == email)
        .order_by(PortalUser.created_at.desc())
    )
    res = await db.execute(stmt)
    portal_user = res.scalars().first()

    if not portal_user or not portal_user.is_active:
        raise UnauthorizedException("Invalid email or password")

    if not verify_password(request.password, portal_user.hashed_password):
        raise UnauthorizedException("Invalid email or password")

    # Update last_login_at
    portal_user.last_login_at = datetime.now(timezone.utc)
    await db.flush()

    # Create dedicated portal access token
    token = create_access_token(
        subject=str(portal_user.id),
        claims={
            "type": "portal",
            "customer_id": str(portal_user.customer_id),
            "organization_id": str(portal_user.organization_id)
        }
    )

    return portal_user, token
