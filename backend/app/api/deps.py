import uuid
from typing import Optional
from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import decode_access_token
from app.core.exceptions import UnauthorizedException, ForbiddenException
from app.models.user import User
from app.models.portal_user import PortalUser

security_scheme = HTTPBearer(
    auto_error=False,
    description="Bearer token authentication using JWT access token"
)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    """FastAPI dependency resolving the current active authenticated user from Bearer token."""
    if not credentials or not credentials.credentials:
        raise UnauthorizedException("Authentication token missing")

    token = credentials.credentials
    payload = decode_access_token(token)

    subject_str = payload.get("sub")
    if not subject_str:
        raise UnauthorizedException("Invalid authentication token payload")

    # Reject portal tokens on internal routes
    if payload.get("type") == "portal":
        raise UnauthorizedException("Portal token not allowed for internal APIs")

    try:
        user_id = uuid.UUID(subject_str)
    except (ValueError, TypeError):
        raise UnauthorizedException("Invalid user identifier in token")

    stmt = (
        select(User)
        .options(selectinload(User.organization))
        .where(User.id == user_id)
    )
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        raise UnauthorizedException("Authenticated user no longer exists")

    if not user.is_active:
        raise UnauthorizedException("User account is inactive")

    if not user.organization or not user.organization.is_active:
        raise UnauthorizedException("User organization is inactive or non-existent")

    return user


async def get_current_portal_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    db: AsyncSession = Depends(get_db)
) -> PortalUser:
    """FastAPI dependency resolving the current active authenticated portal user from Bearer token."""
    if not credentials or not credentials.credentials:
        raise UnauthorizedException("Portal authentication token missing")

    token = credentials.credentials
    payload = decode_access_token(token)

    if payload.get("type") != "portal":
        raise UnauthorizedException("Invalid portal authentication token")

    subject_str = payload.get("sub")
    if not subject_str:
        raise UnauthorizedException("Invalid token payload")

    try:
        portal_user_id = uuid.UUID(subject_str)
    except (ValueError, TypeError):
        raise UnauthorizedException("Invalid portal user identifier")

    stmt = (
        select(PortalUser)
        .options(
            selectinload(PortalUser.customer),
            selectinload(PortalUser.organization)
        )
        .where(PortalUser.id == portal_user_id)
    )
    res = await db.execute(stmt)
    portal_user = res.scalar_one_or_none()

    if not portal_user or not portal_user.is_active:
        raise UnauthorizedException("Portal user account is inactive or non-existent")

    if not portal_user.organization or not portal_user.organization.is_active:
        raise UnauthorizedException("Portal user organization is inactive")

    return portal_user


def is_admin_user(user: User) -> bool:
    """Helper function checking if user has administrator privileges."""
    return bool(user and user.is_admin)


async def require_admin(
    current_user: User = Depends(get_current_user)
) -> User:
    """FastAPI authorization dependency requiring administrator privileges (HTTP 403 Forbidden on failure)."""
    if not is_admin_user(current_user):
        raise ForbiddenException("Administrator privileges required")
    return current_user
