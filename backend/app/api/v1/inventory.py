from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.inventory import (
    WarehouseCreate,
    WarehouseResponse,
    ProductVariantCreate,
    ProductVariantResponse,
    StockReceiptRequest,
    InventoryStockResponse,
    InventoryMovementResponse,
    QuotationAvailabilitySummary,
)
from app.services import inventory as inventory_service
from app.services import reservations as reservation_service

router = APIRouter()


@router.post("/warehouses", response_model=WarehouseResponse, status_code=status.HTTP_201_CREATED)
async def create_warehouse(
    payload: WarehouseCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await inventory_service.create_warehouse(db, current_user.organization_id, payload)


@router.get("/warehouses", response_model=List[WarehouseResponse])
async def list_warehouses(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await inventory_service.get_warehouses(db, current_user.organization_id)


@router.post("/variants", response_model=ProductVariantResponse, status_code=status.HTTP_201_CREATED)
async def create_product_variant(
    payload: ProductVariantCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await inventory_service.create_product_variant(db, current_user.organization_id, payload)


@router.post("/stocks/receipt", response_model=InventoryStockResponse)
async def record_stock_receipt(
    payload: StockReceiptRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await inventory_service.record_stock_receipt(
        db, current_user.organization_id, payload, current_user.id, current_user.full_name
    )


@router.get("/stocks", response_model=List[InventoryStockResponse])
async def list_inventory_stocks(
    warehouse_id: Optional[UUID] = Query(None),
    product_id: Optional[UUID] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await inventory_service.get_inventory_stocks(db, current_user.organization_id, warehouse_id, product_id)


@router.get("/movements", response_model=List[InventoryMovementResponse])
async def list_inventory_movements(
    warehouse_id: Optional[UUID] = Query(None),
    product_id: Optional[UUID] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await inventory_service.get_inventory_movements(db, current_user.organization_id, warehouse_id, product_id)



@router.get("/availability/quotations/{quotation_id}", response_model=QuotationAvailabilitySummary)
async def get_quotation_availability(
    quotation_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await inventory_service.calculate_quotation_availability(db, current_user.organization_id, quotation_id)


@router.post("/reservations/quotations/{quotation_id}")
async def reserve_quotation_stock(
    quotation_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await reservation_service.reserve_stock_for_quotation(
        db, current_user.organization_id, quotation_id, current_user.id, current_user.full_name
    )


@router.post("/reservations/quotations/{quotation_id}/release")
async def release_quotation_stock(
    quotation_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    released_count = await reservation_service.release_quotation_reservations(
        db, current_user.organization_id, quotation_id, current_user.id, current_user.full_name
    )
    return {"message": "Stock reservations released successfully", "released_count": released_count}
