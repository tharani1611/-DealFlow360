import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_user, require_admin
from app.models.user import User
from app.schemas.discount_governance import (
    DiscountPolicyCreate, DiscountPolicyUpdate, DiscountPolicyResponse, GovernanceEvaluationResult
)
from app.services import discount_governance as governance_service

router = APIRouter()


@router.post(
    "/policies",
    response_model=DiscountPolicyResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Discount Policy",
    description="Creates a new discount governance policy for the organization (requires Admin role)."
)
async def create_policy(
    payload: DiscountPolicyCreate,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
) -> DiscountPolicyResponse:
    return await governance_service.create_discount_policy(db, current_user.organization_id, payload)


@router.get(
    "/policies",
    response_model=List[DiscountPolicyResponse],
    status_code=status.HTTP_200_OK,
    summary="List Discount Policies",
    description="Retrieves discount governance policies for the current organization."
)
async def list_policies(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    scope: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> List[DiscountPolicyResponse]:
    return await governance_service.list_discount_policies(
        db, current_user.organization_id, skip=skip, limit=limit, scope=scope, is_active=is_active
    )


@router.get(
    "/policies/{policy_id}",
    response_model=DiscountPolicyResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Discount Policy Details",
    description="Fetches a specific discount policy by ID."
)
async def get_policy(
    policy_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> DiscountPolicyResponse:
    return await governance_service.get_discount_policy_by_id(db, current_user.organization_id, policy_id)


@router.put(
    "/policies/{policy_id}",
    response_model=DiscountPolicyResponse,
    status_code=status.HTTP_200_OK,
    summary="Update Discount Policy",
    description="Updates a discount governance policy (requires Admin role)."
)
async def update_policy(
    policy_id: uuid.UUID,
    payload: DiscountPolicyUpdate,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
) -> DiscountPolicyResponse:
    return await governance_service.update_discount_policy(db, current_user.organization_id, policy_id, payload)


@router.delete(
    "/policies/{policy_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Discount Policy",
    description="Deletes a discount governance policy (requires Admin role)."
)
async def delete_policy(
    policy_id: uuid.UUID,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
) -> None:
    await governance_service.delete_discount_policy(db, current_user.organization_id, policy_id)


@router.post(
    "/evaluate",
    response_model=GovernanceEvaluationResult,
    status_code=status.HTTP_200_OK,
    summary="Evaluate Discount Governance",
    description="Evaluates discount compliance against active policies for a quotation or preview items."
)
async def evaluate_governance(
    quotation_id: Optional[uuid.UUID] = Query(None),
    customer_id: Optional[uuid.UUID] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> GovernanceEvaluationResult:
    return await governance_service.evaluate_discount_governance(
        db,
        current_user.organization_id,
        quotation_id=quotation_id,
        customer_id=customer_id,
        user_id=current_user.id,
        user_role="admin" if current_user.is_admin else "user"
    )
