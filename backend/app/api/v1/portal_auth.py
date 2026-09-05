from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.portal import PortalLoginRequest, PortalTokenResponse, PortalUserResponse
from app.services import portal_auth
from app.api.deps import get_current_portal_user
from app.models.portal_user import PortalUser

router = APIRouter(prefix="/portal/auth", tags=["Customer Portal Auth"])


@router.post("/login", response_model=PortalTokenResponse)
async def login_portal_user(
    payload: PortalLoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """Authenticates customer portal user with email and password."""
    portal_user, token = await portal_auth.authenticate_portal_user(db, payload)
    return PortalTokenResponse(
        access_token=token,
        token_type="bearer",
        portal_user=PortalUserResponse.model_validate(portal_user)
    )


@router.get("/me", response_model=PortalUserResponse)
async def get_portal_me(
    current_portal_user: PortalUser = Depends(get_current_portal_user)
):
    """Returns currently authenticated customer portal user profile."""
    return PortalUserResponse.model_validate(current_portal_user)
