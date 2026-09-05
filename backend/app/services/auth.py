from typing import Tuple
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
import logging

from app.models.organization import Organization
from app.models.user import User
from app.schemas.auth import RegisterRequest, LoginRequest
from app.core.security import hash_password, verify_password, create_access_token
from app.core.exceptions import UnauthorizedException, ConflictException, BusinessRuleViolationException

logger = logging.getLogger("dealflow360.auth_service")


async def register_user_and_organization(
    db: AsyncSession,
    request: RegisterRequest
) -> Tuple[User, Organization, str]:
    """Atomically creates a new Organization and its initial admin User."""
    slug = request.organization_slug.strip().lower()
    email = request.email.strip().lower()

    # Pre-check for duplicate organization slug
    existing_org = await db.execute(select(Organization).where(Organization.slug == slug))
    if existing_org.scalar_one_or_none():
        raise ConflictException(f"Organization slug '{slug}' is already taken.")

    hashed_pwd = hash_password(request.password)

    organization = Organization(
        name=request.organization_name.strip(),
        slug=slug,
        is_active=True
    )

    try:
        db.add(organization)
        await db.flush()  # Obtain generated organization.id within transaction

        user = User(
            organization_id=organization.id,
            email=email,
            full_name=request.full_name.strip() if request.full_name else None,
            password_hash=hashed_pwd,
            is_active=True,
            is_admin=True
        )

        db.add(user)
        await db.flush()  # Validate user constraints within transaction
    except IntegrityError as exc:
        await db.rollback()
        error_msg = str(exc)
        logger.warning(f"Registration transaction failed for slug '{slug}', email '{email}': {error_msg}")
        if "uq_users_organization_id_email" in error_msg:
            raise ConflictException(f"User with email '{email}' already exists in this organization.")
        if "organizations_slug" in error_msg or "slug" in error_msg:
            raise ConflictException(f"Organization slug '{slug}' is already taken.")
        raise BusinessRuleViolationException("Registration failed due to a database constraint violation.")

    # Attach organization relationship in memory
    user.organization = organization

    # Generate access token
    token = create_access_token(subject=str(user.id))
    return user, organization, token


async def authenticate_user(
    db: AsyncSession,
    request: LoginRequest
) -> Tuple[User, Organization, str]:
    """Authenticates a user using organization slug, email, and password."""
    slug = request.organization_slug.strip().lower()
    email = request.email.strip().lower()

    # 1. Fetch organization by slug
    org_stmt = select(Organization).where(Organization.slug == slug)
    org_res = await db.execute(org_stmt)
    organization = org_res.scalar_one_or_none()

    # Generic 401 on missing or inactive organization
    if not organization or not organization.is_active:
        raise UnauthorizedException("Invalid organization, email, or password")

    # 2. Fetch user by organization_id + email
    user_stmt = select(User).where(User.organization_id == organization.id, User.email == email)
    user_res = await db.execute(user_stmt)
    user = user_res.scalar_one_or_none()

    # Generic 401 on missing or inactive user
    if not user or not user.is_active:
        raise UnauthorizedException("Invalid organization, email, or password")

    # 3. Verify password
    if not verify_password(request.password, user.password_hash):
        raise UnauthorizedException("Invalid organization, email, or password")

    user.organization = organization

    # Generate access token
    token = create_access_token(subject=str(user.id))
    return user, organization, token
