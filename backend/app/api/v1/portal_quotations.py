import uuid
from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_portal_user
from app.models.portal_user import PortalUser
from app.schemas.portal import (
    PortalQuotationListItemResponse, PortalQuotationDetailResponse, PortalAcceptRejectRequest, PortalActionResponse
)
from app.schemas.negotiation import ChangeRequestCreate, ChangeRequestResponse, LineCommentCreate, LineCommentResponse
from app.services import portal_quotations, negotiation

router = APIRouter(prefix="/portal/quotations", tags=["Customer Portal Quotations"])


@router.get("", response_model=List[PortalQuotationListItemResponse])
async def list_portal_quotations(
    current_portal_user: PortalUser = Depends(get_current_portal_user),
    db: AsyncSession = Depends(get_db)
):
    """Lists published customer quotations for current portal user."""
    return await portal_quotations.list_portal_quotations(db, current_portal_user)


@router.get("/{quotation_id}", response_model=PortalQuotationDetailResponse)
async def get_portal_quotation_detail(
    quotation_id: uuid.UUID,
    current_portal_user: PortalUser = Depends(get_current_portal_user),
    db: AsyncSession = Depends(get_db)
):
    """Retrieves sanitized quotation detail for current portal user."""
    return await portal_quotations.get_portal_quotation_detail(db, current_portal_user, quotation_id)


@router.post("/{quotation_id}/accept", response_model=PortalActionResponse)
async def accept_portal_quotation(
    quotation_id: uuid.UUID,
    payload: PortalAcceptRejectRequest,
    current_portal_user: PortalUser = Depends(get_current_portal_user),
    db: AsyncSession = Depends(get_db)
):
    """Customer accepts the quotation in portal."""
    return await portal_quotations.accept_portal_quotation(db, current_portal_user, quotation_id, payload.reason)


@router.post("/{quotation_id}/reject", response_model=PortalActionResponse)
async def reject_portal_quotation(
    quotation_id: uuid.UUID,
    payload: PortalAcceptRejectRequest,
    current_portal_user: PortalUser = Depends(get_current_portal_user),
    db: AsyncSession = Depends(get_db)
):
    """Customer rejects the quotation in portal."""
    return await portal_quotations.reject_portal_quotation(db, current_portal_user, quotation_id, payload.reason)


@router.post("/{quotation_id}/change-requests", response_model=ChangeRequestResponse, status_code=status.HTTP_201_CREATED)
async def create_portal_change_request(
    quotation_id: uuid.UUID,
    payload: ChangeRequestCreate,
    current_portal_user: PortalUser = Depends(get_current_portal_user),
    db: AsyncSession = Depends(get_db)
):
    """Customer submits a change request / counter discount proposal from portal."""
    cr = await negotiation.create_change_request(db, current_portal_user, quotation_id, payload)
    return ChangeRequestResponse.model_validate(cr)


@router.get("/{quotation_id}/comments", response_model=List[LineCommentResponse])
async def list_portal_line_comments(
    quotation_id: uuid.UUID,
    current_portal_user: PortalUser = Depends(get_current_portal_user),
    db: AsyncSession = Depends(get_db)
):
    """Lists client-visible line comments for portal user."""
    comments = await negotiation.list_line_comments(
        db=db,
        organization_id=current_portal_user.organization_id,
        quotation_id=quotation_id,
        is_portal=True
    )
    return [LineCommentResponse.model_validate(c) for c in comments]


@router.post("/{quotation_id}/comments", response_model=LineCommentResponse, status_code=status.HTTP_201_CREATED)
async def create_portal_line_comment(
    quotation_id: uuid.UUID,
    payload: LineCommentCreate,
    current_portal_user: PortalUser = Depends(get_current_portal_user),
    db: AsyncSession = Depends(get_db)
):
    """Customer posts a line comment from portal."""
    comment = await negotiation.create_line_comment(
        db=db,
        organization_id=current_portal_user.organization_id,
        quotation_id=quotation_id,
        payload=payload,
        author_portal_user=current_portal_user
    )
    return LineCommentResponse.model_validate(comment)
