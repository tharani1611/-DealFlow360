from uuid import UUID
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.inventory import BillingClassificationResponse
from app.services import hybrid_billing as billing_service

router = APIRouter()


@router.get("/quotations/{quotation_id}", response_model=BillingClassificationResponse)
async def classify_hybrid_billing(
    quotation_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await billing_service.classify_quotation_hybrid_billing(db, current_user.organization_id, quotation_id)
