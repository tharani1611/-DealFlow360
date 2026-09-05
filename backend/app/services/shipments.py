import uuid
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app.models.fulfillment import Shipment, ShipmentLine, WarehouseAllocation
from app.models.inventory import InventoryStock, InventoryMovement, InventoryReservation
from app.models.quotation import Quotation, QuotationItem
from app.schemas.inventory import ShipmentCreateRequest
from app.core.exceptions import NotFoundException, BusinessRuleViolationException


async def create_shipment_from_allocation(
    session: AsyncSession,
    organization_id: uuid.UUID,
    payload: ShipmentCreateRequest,
    actor_id: Optional[uuid.UUID] = None,
    actor_name: Optional[str] = None,
) -> Shipment:
    """Create a physical shipment record from warehouse allocations, consuming reserved stock."""
    # 1. Check quotation
    q_stmt = select(Quotation).where(Quotation.id == payload.quotation_id, Quotation.organization_id == organization_id)
    q_res = await session.execute(q_stmt)
    quotation = q_res.scalar_one_or_none()
    if not quotation:
        raise NotFoundException(f"Quotation {payload.quotation_id} not found")

    # 2. Get allocations for target warehouse
    alloc_stmt = select(WarehouseAllocation).where(
        WarehouseAllocation.organization_id == organization_id,
        WarehouseAllocation.quotation_id == payload.quotation_id,
        WarehouseAllocation.warehouse_id == payload.warehouse_id,
        WarehouseAllocation.status == "ALLOCATED",
    )
    allocations = list((await session.execute(alloc_stmt)).scalars().all())
    if not allocations:
        raise BusinessRuleViolationException(f"No active warehouse allocations found for warehouse {payload.warehouse_id}")

    # Generate unique shipment number
    shipment_num = f"SHP-{quotation.quotation_number.replace('QT-', '')}-{uuid.uuid4().hex[:4].upper()}"

    shipment = Shipment(
        organization_id=organization_id,
        shipment_number=shipment_num,
        quotation_id=payload.quotation_id,
        warehouse_id=payload.warehouse_id,
        status="DRAFT",
        carrier=payload.carrier,
        tracking_number=payload.tracking_number,
        expected_delivery_date=payload.expected_delivery_date,
    )
    session.add(shipment)
    await session.flush()

    for alloc in allocations:
        # Fetch item details
        item_stmt = select(QuotationItem).where(QuotationItem.id == alloc.quotation_item_id)
        item = (await session.execute(item_stmt)).scalar_one_or_none()
        if not item:
            continue

        shipment_line = ShipmentLine(
            organization_id=organization_id,
            shipment_id=shipment.id,
            quotation_item_id=alloc.quotation_item_id,
            product_id=item.product_id,
            variant_id=None,
            quantity=alloc.allocated_quantity,
        )
        session.add(shipment_line)

        # Mark allocation fulfilled
        alloc.status = "FULFILLED"

        # Consume reservation & update on-hand stock balance
        stock_stmt = (
            select(InventoryStock)
            .where(
                InventoryStock.organization_id == organization_id,
                InventoryStock.warehouse_id == payload.warehouse_id,
                InventoryStock.product_id == item.product_id,
            )
            .with_for_update()
        )
        stock = (await session.execute(stock_stmt)).scalar_one_or_none()
        if stock:
            stock.on_hand_quantity = max(0, stock.on_hand_quantity - alloc.allocated_quantity)
            stock.reserved_quantity = max(0, stock.reserved_quantity - alloc.allocated_quantity)
            stock.available_quantity = stock.on_hand_quantity - stock.reserved_quantity

        # Record movement
        movement = InventoryMovement(
            organization_id=organization_id,
            warehouse_id=payload.warehouse_id,
            product_id=item.product_id,
            quantity=alloc.allocated_quantity,
            movement_type="SHIPMENT",
            reference_type="SHIPMENT",
            reference_id=shipment.id,
            actor_id=actor_id,
            actor_name=actor_name,
            notes=f"Shipped under {shipment_num}",
        )
        session.add(movement)

    await session.commit()
    await session.refresh(shipment)
    return shipment


async def update_shipment_status(
    session: AsyncSession,
    organization_id: uuid.UUID,
    shipment_id: uuid.UUID,
    new_status: str,
) -> Shipment:
    """Transition shipment lifecycle status (e.g., READY -> SHIPPED -> IN_TRANSIT -> DELIVERED)."""
    stmt = select(Shipment).where(Shipment.id == shipment_id, Shipment.organization_id == organization_id)
    shipment = (await session.execute(stmt)).scalar_one_or_none()
    if not shipment:
        raise NotFoundException(f"Shipment {shipment_id} not found")

    shipment.status = new_status.upper()
    if new_status.upper() == "SHIPPED" and not shipment.shipped_at:
        shipment.shipped_at = datetime.now(timezone.utc)
    elif new_status.upper() == "DELIVERED":
        shipment.actual_delivery_date = datetime.now(timezone.utc).date()

    await session.commit()
    await session.refresh(shipment)
    return shipment


async def get_shipments_for_quotation(
    session: AsyncSession,
    organization_id: uuid.UUID,
    quotation_id: uuid.UUID,
) -> List[Shipment]:
    """List all shipments for a quotation with lines."""
    stmt = select(Shipment).where(Shipment.organization_id == organization_id, Shipment.quotation_id == quotation_id)
    result = await session.execute(stmt)
    return list(result.scalars().all())
