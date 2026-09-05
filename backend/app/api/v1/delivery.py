from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.inventory import DeliveryPromiseResponse
from app.services import delivery_promise as delivery_service

router = APIRouter()


@router.post("/quotations/{quotation_id}", response_model=DeliveryPromiseResponse)
async def calculate_delivery_promise(
    quotation_id: UUID,
    lead_time_days: int = Query(7, ge=1, le=90),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await delivery_service.calculate_or_update_delivery_promise(db, current_user.organization_id, quotation_id, lead_time_days)


@router.get("", response_model=List[DeliveryPromiseResponse])
async def list_delivery_promises(
    status: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await delivery_service.get_delivery_promises_for_organization(db, current_user.organization_id, status)
