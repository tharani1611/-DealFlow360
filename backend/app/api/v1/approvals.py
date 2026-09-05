import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_user, require_admin
from app.models.user import User
from app.schemas.approval_engine import (
    ApprovalRuleCreate, ApprovalRuleUpdate, ApprovalRuleResponse,
    ApprovalDecisionRequest, QuotationApprovalResponse
)
from app.services import approval_engine as approval_service

router = APIRouter()


@router.post(
    "/rules",
    response_model=ApprovalRuleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Approval Rule",
    description="Creates a new approval rule (requires Admin role)."
)
async def create_rule(
    payload: ApprovalRuleCreate,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
) -> ApprovalRuleResponse:
    return await approval_service.create_approval_rule(db, current_user.organization_id, payload)


@router.get(
    "/rules",
    response_model=List[ApprovalRuleResponse],
    status_code=status.HTTP_200_OK,
    summary="List Approval Rules",
    description="Retrieves approval rules for the organization."
)
async def list_rules(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    is_active: Optional[bool] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> List[ApprovalRuleResponse]:
    return await approval_service.list_approval_rules(
        db, current_user.organization_id, skip=skip, limit=limit, is_active=is_active
    )


@router.get(
    "/rules/{rule_id}",
    response_model=ApprovalRuleResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Approval Rule Details",
    description="Fetches an approval rule by ID."
)
async def get_rule(
    rule_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> ApprovalRuleResponse:
    return await approval_service.get_approval_rule_by_id(db, current_user.organization_id, rule_id)


@router.put(
    "/rules/{rule_id}",
    response_model=ApprovalRuleResponse,
    status_code=status.HTTP_200_OK,
    summary="Update Approval Rule",
    description="Updates an approval rule (requires Admin role)."
)
async def update_rule(
    rule_id: uuid.UUID,
    payload: ApprovalRuleUpdate,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
) -> ApprovalRuleResponse:
    return await approval_service.update_approval_rule(db, current_user.organization_id, rule_id, payload)


@router.delete(
    "/rules/{rule_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Approval Rule",
    description="Deletes an approval rule (requires Admin role)."
)
async def delete_rule(
    rule_id: uuid.UUID,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
) -> None:
    await approval_service.delete_approval_rule(db, current_user.organization_id, rule_id)


@router.post(
    "/quotations/{quotation_id}/decision",
    response_model=QuotationApprovalResponse,
    status_code=status.HTTP_200_OK,
    summary="Submit Approval Decision",
    description="Submits an approval decision ('APPROVED' or 'REJECTED') for a quotation (requires Admin role)."
)
async def submit_approval_decision(
    quotation_id: uuid.UUID,
    payload: ApprovalDecisionRequest,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
) -> QuotationApprovalResponse:
    rec = await approval_service.record_approval_decision(
        db,
        current_user.organization_id,
        quotation_id,
        current_user,
        payload.decision,
        note=payload.note
    )
    req_name = rec.requested_by_user.full_name or rec.requested_by_user.email if rec.requested_by_user else None
    appr_name = rec.approved_by_user.full_name or rec.approved_by_user.email if rec.approved_by_user else None

    return QuotationApprovalResponse(
        id=rec.id,
        organization_id=rec.organization_id,
        quotation_id=rec.quotation_id,
        approval_rule_id=rec.approval_rule_id,
        requested_by_user_id=rec.requested_by_user_id,
        requested_by_user_name=req_name,
        approved_by_user_id=rec.approved_by_user_id,
        approved_by_user_name=appr_name,
        status=rec.status,
        approval_level=rec.approval_level,
        reasons=rec.reasons,
        decision_note=rec.decision_note,
        created_at=rec.created_at,
        updated_at=rec.updated_at
    )
