import uuid
from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.discount_risk import RiskEvaluationResult
from app.services import discount_risk as risk_service

router = APIRouter()


@router.post(
    "/evaluate",
    response_model=RiskEvaluationResult,
    status_code=status.HTTP_200_OK,
    summary="Evaluate Commercial Risk",
    description="Evaluates commercial risk score and classification for a quotation."
)
async def evaluate_risk(
    quotation_id: Optional[uuid.UUID] = Query(None),
    customer_id: Optional[uuid.UUID] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> RiskEvaluationResult:
    return await risk_service.evaluate_discount_risk(
        db,
        current_user.organization_id,
        quotation_id=quotation_id,
        customer_id=customer_id,
        user_id=current_user.id,
        user_role="admin" if current_user.is_admin else "user"
    )
