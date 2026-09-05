from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.inventory import (
    SmartAllocationSummary,
    ManualOverrideRequest,
    WarehouseAllocationResponse,
)
from app.services import fulfillment_allocation as allocation_service

router = APIRouter()


@router.post("/quotations/{quotation_id}/allocate", response_model=SmartAllocationSummary)
async def calculate_smart_allocation(
    quotation_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await allocation_service.calculate_smart_warehouse_allocation(db, current_user.organization_id, quotation_id)


@router.post("/override", response_model=WarehouseAllocationResponse)
async def apply_manual_override(
    payload: ManualOverrideRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await allocation_service.apply_manual_fulfillment_override(db, current_user.organization_id, payload, current_user)
