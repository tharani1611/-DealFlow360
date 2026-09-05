from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.inventory import ShipmentCreateRequest, ShipmentResponse
from app.services import shipments as shipment_service

router = APIRouter()


@router.post("", response_model=ShipmentResponse, status_code=status.HTTP_201_CREATED)
async def create_shipment(
    payload: ShipmentCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await shipment_service.create_shipment_from_allocation(
        db, current_user.organization_id, payload, current_user.id, current_user.full_name
    )


@router.get("/quotations/{quotation_id}", response_model=List[ShipmentResponse])
async def list_shipments_for_quotation(
    quotation_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await shipment_service.get_shipments_for_quotation(db, current_user.organization_id, quotation_id)


@router.patch("/{shipment_id}/status", response_model=ShipmentResponse)
async def update_shipment_status(
    shipment_id: UUID,
    new_status: str = Query(..., description="DRAFT, READY, PACKED, SHIPPED, IN_TRANSIT, DELIVERED, CANCELLED"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await shipment_service.update_shipment_status(db, current_user.organization_id, shipment_id, new_status)
