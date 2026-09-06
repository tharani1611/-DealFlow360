import uuid
from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.negotiation import (
    ApprovalAuditLogResponse, LineCommentCreate, LineCommentResponse,
    ChangeRequestResponse, ChangeRequestReview, CounterDiscountApply, QuotationVersionResponse
)
from app.schemas.co_negotiator import NegotiationSimulationRequest, NegotiationSimulationResponse
from app.schemas.quotation import QuotationResponse
from app.services import negotiation, approval_engine, co_negotiator

router = APIRouter(prefix="/quotations", tags=["Quotation Negotiation & Approval Audit"])


@router.get("/{quotation_id}/audit-logs", response_model=List[ApprovalAuditLogResponse])
async def get_approval_audit_logs(
    quotation_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Lists approval audit logs for a quotation."""
    logs = await approval_engine.get_approval_audit_logs(db, current_user.organization_id, quotation_id)
    return [ApprovalAuditLogResponse.model_validate(l) for l in logs]


@router.get("/{quotation_id}/comments", response_model=List[LineCommentResponse])
async def list_internal_line_comments(
    quotation_id: uuid.UUID,
    quotation_item_id: uuid.UUID = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Lists line comments for internal sales user (includes internal-only comments)."""
    comments = await negotiation.list_line_comments(
        db=db,
        organization_id=current_user.organization_id,
        quotation_id=quotation_id,
        quotation_item_id=quotation_item_id,
        is_portal=False
    )
    return [LineCommentResponse.model_validate(c) for c in comments]


@router.post("/{quotation_id}/comments", response_model=LineCommentResponse, status_code=status.HTTP_201_CREATED)
async def create_internal_line_comment(
    quotation_id: uuid.UUID,
    payload: LineCommentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Creates a line comment from an internal sales user."""
    comment = await negotiation.create_line_comment(
        db=db,
        organization_id=current_user.organization_id,
        quotation_id=quotation_id,
        payload=payload,
        author_user=current_user
    )
    return LineCommentResponse.model_validate(comment)


@router.get("/{quotation_id}/change-requests", response_model=List[ChangeRequestResponse])
async def list_change_requests(
    quotation_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Lists customer change requests for a quotation."""
    crs = await negotiation.list_change_requests(db, current_user.organization_id, quotation_id)
    return [ChangeRequestResponse.model_validate(cr) for cr in crs]


@router.post("/{quotation_id}/change-requests/{change_request_id}/review", response_model=ChangeRequestResponse)
async def review_change_request(
    quotation_id: uuid.UUID,
    change_request_id: uuid.UUID,
    payload: ChangeRequestReview,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Reviews (accepts or rejects) a customer change request."""
    cr = await negotiation.review_change_request(
        db=db,
        organization_id=current_user.organization_id,
        quotation_id=quotation_id,
        change_request_id=change_request_id,
        reviewer_user=current_user,
        payload=payload
    )
    return ChangeRequestResponse.model_validate(cr)


@router.post("/{quotation_id}/counter-discount", response_model=QuotationResponse)
async def apply_counter_discount(
    quotation_id: uuid.UUID,
    payload: CounterDiscountApply,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Applies counter-discount adjustments, recalculates pricing, invalidates approval, and creates version snapshot."""
    q = await negotiation.apply_counter_discount(
        db=db,
        organization_id=current_user.organization_id,
        quotation_id=quotation_id,
        user=current_user,
        payload=payload
    )
    return QuotationResponse.model_validate(q)


@router.get("/{quotation_id}/versions", response_model=List[QuotationVersionResponse])
async def list_quotation_versions(
    quotation_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Lists historical versions and snapshots for a quotation."""
    versions = await negotiation.list_quotation_versions(db, current_user.organization_id, quotation_id)
    return [QuotationVersionResponse.model_validate(v) for v in versions]


@router.post("/{quotation_id}/simulate-counter-offer", response_model=NegotiationSimulationResponse)
async def simulate_counter_offer(
    quotation_id: uuid.UUID,
    payload: NegotiationSimulationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Simulates 120+ commercial negotiation scenarios and returns optimal counter-offer recommendations."""
    return await co_negotiator.simulate_negotiation_scenarios(
        session=db,
        organization_id=current_user.organization_id,
        quotation_id=quotation_id,
        payload=payload
    )

