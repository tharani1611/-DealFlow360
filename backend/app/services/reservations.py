import uuid
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_
from app.models.inventory import InventoryStock, InventoryMovement, InventoryReservation
from app.models.warehouses import Warehouse
from app.models.quotation import Quotation, QuotationItem
from app.core.exceptions import NotFoundException, BusinessRuleViolationException


async def reserve_stock_for_quotation(
    session: AsyncSession,
    organization_id: uuid.UUID,
    quotation_id: uuid.UUID,
    actor_id: Optional[uuid.UUID] = None,
    actor_name: Optional[str] = None,
) -> List[InventoryReservation]:
    """Reserve available inventory for an accepted quotation using row-level locking."""
    # 1. Verify quotation exists
    q_stmt = select(Quotation).where(Quotation.id == quotation_id, Quotation.organization_id == organization_id)
    q_res = await session.execute(q_stmt)
    quotation = q_res.scalar_one_or_none()
    if not quotation:
        raise NotFoundException(f"Quotation {quotation_id} not found")

    # 2. Fetch quotation items
    items_stmt = select(QuotationItem).where(QuotationItem.quotation_id == quotation_id)
    items = list((await session.execute(items_stmt)).scalars().all())

    reservations: List[InventoryReservation] = []

    # Get priority warehouses
    wh_stmt = select(Warehouse).where(
        Warehouse.organization_id == organization_id,
        Warehouse.is_active == True
    ).order_by(Warehouse.priority.asc())
    warehouses = list((await session.execute(wh_stmt)).scalars().all())

    if not warehouses:
        raise BusinessRuleViolationException("No active warehouse registered in organization for reservation")

    for item in items:
        qty_to_reserve = item.quantity

        for wh in warehouses:
            if qty_to_reserve <= 0:
                break

            # Row lock stock record
            stock_stmt = (
                select(InventoryStock)
                .where(
                    InventoryStock.organization_id == organization_id,
                    InventoryStock.warehouse_id == wh.id,
                    InventoryStock.product_id == item.product_id,
                )
                .with_for_update()
            )
            stock_res = await session.execute(stock_stmt)
            stock = stock_res.scalar_one_or_none()

            if stock and stock.available_quantity > 0:
                allocable = min(qty_to_reserve, stock.available_quantity)

                # Mutate stock
                stock.reserved_quantity += allocable
                stock.available_quantity = stock.on_hand_quantity - stock.reserved_quantity

                # Record reservation
                res = InventoryReservation(
                    organization_id=organization_id,
                    quotation_id=quotation_id,
                    quotation_item_id=item.id,
                    product_id=item.product_id,
                    warehouse_id=wh.id,
                    quantity=allocable,
                    status="ACTIVE",
                )
                session.add(res)
                reservations.append(res)

                # Record movement
                movement = InventoryMovement(
                    organization_id=organization_id,
                    warehouse_id=wh.id,
                    product_id=item.product_id,
                    quantity=allocable,
                    movement_type="RESERVATION",
                    reference_type="QUOTATION",
                    reference_id=quotation_id,
                    actor_id=actor_id,
                    actor_name=actor_name,
                    notes=f"Reserved for Quotation {quotation.quotation_number}",
                )
                session.add(movement)

                qty_to_reserve -= allocable

    await session.commit()
    for r in reservations:
        await session.refresh(r)
    return reservations


async def release_quotation_reservations(
    session: AsyncSession,
    organization_id: uuid.UUID,
    quotation_id: uuid.UUID,
    actor_id: Optional[uuid.UUID] = None,
    actor_name: Optional[str] = None,
) -> int:
    """Release active inventory reservations for a quotation (e.g. on cancellation)."""
    res_stmt = select(InventoryReservation).where(
        InventoryReservation.organization_id == organization_id,
        InventoryReservation.quotation_id == quotation_id,
        InventoryReservation.status == "ACTIVE",
    )
    reservations = list((await session.execute(res_stmt)).scalars().all())

    released_count = 0
    for res in reservations:
        stock_stmt = (
            select(InventoryStock)
            .where(
                InventoryStock.organization_id == organization_id,
                InventoryStock.warehouse_id == res.warehouse_id,
                InventoryStock.product_id == res.product_id,
            )
            .with_for_update()
        )
        stock = (await session.execute(stock_stmt)).scalar_one_or_none()
        if stock:
            stock.reserved_quantity = max(0, stock.reserved_quantity - res.quantity)
            stock.available_quantity = stock.on_hand_quantity - stock.reserved_quantity

        res.status = "RELEASED"

        movement = InventoryMovement(
            organization_id=organization_id,
            warehouse_id=res.warehouse_id,
            product_id=res.product_id,
            quantity=res.quantity,
            movement_type="RELEASE",
            reference_type="QUOTATION",
            reference_id=quotation_id,
            actor_id=actor_id,
            actor_name=actor_name,
            notes=f"Reservation released for Quotation {quotation_id}",
        )
        session.add(movement)
        released_count += 1

    await session.commit()
    return released_count


async def get_quotation_reservations(
    session: AsyncSession,
    organization_id: uuid.UUID,
    quotation_id: uuid.UUID,
) -> List[InventoryReservation]:
    """Retrieve all reservations for a quotation."""
    stmt = select(InventoryReservation).where(
        InventoryReservation.organization_id == organization_id,
        InventoryReservation.quotation_id == quotation_id,
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())
