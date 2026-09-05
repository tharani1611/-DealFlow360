from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.auth import (
    RegisterRequest,
    RegisterResponse,
    LoginRequest,
    AuthResponse,
    UserResponse,
)
from app.services import auth as auth_service
from app.api.deps import get_current_user, require_admin
from app.models.user import User

router = APIRouter()


@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register Organization & Admin User",
    description="Atomically creates a new Organization and its primary administrator User."
)
async def register(
    request: RegisterRequest,
    db: AsyncSession = Depends(get_db)
) -> RegisterResponse:
    """Registers a new Organization and its initial administrator user."""
    user, organization, access_token = await auth_service.register_user_and_organization(db, request)
    return RegisterResponse(
        user=user,
        organization=organization,
        access_token=access_token,
        token_type="bearer"
    )


@router.post(
    "/login",
    response_model=AuthResponse,
    status_code=status.HTTP_200_OK,
    summary="Authenticate User",
    description="Authenticates a user against an organization_slug, email, and password."
)
async def login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db)
) -> AuthResponse:
    """Authenticates user credentials against the organization context."""
    user, organization, access_token = await auth_service.authenticate_user(db, request)
    return AuthResponse(
        access_token=access_token,
        token_type="bearer",
        user=user,
        organization=organization
    )


@router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Current Authenticated User",
    description="Returns authenticated user and tenant organization details from Bearer token."
)
async def get_me(
    current_user: User = Depends(get_current_user)
) -> UserResponse:
    """Returns profile information of the current authenticated user."""
    return current_user


@router.get(
    "/admin-check",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Diagnostic Admin Authorization Check",
    description="Development/diagnostic endpoint verifying administrator authorization (requires require_admin dependency)."
)
async def admin_check(
    current_admin: User = Depends(require_admin)
) -> dict:
    """Diagnostic endpoint verifying administrator authorization status."""
    return {
        "authorized": True,
        "role": current_admin.role,
        "user_id": str(current_admin.id),
        "organization_id": str(current_admin.organization_id)
    }
