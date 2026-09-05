from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.inventory import BackorderResponse, BackorderConsolidationSummary
from app.services import backorders as backorder_service

router = APIRouter()


@router.get("", response_model=List[BackorderResponse])
async def list_organization_backorders(
    status: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await backorder_service.get_organization_backorders(db, current_user.organization_id, status)


@router.get("/customers/{customer_id}/consolidation", response_model=BackorderConsolidationSummary)
async def get_customer_backorder_consolidation(
    customer_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await backorder_service.get_customer_backorder_consolidation(db, current_user.organization_id, customer_id)
