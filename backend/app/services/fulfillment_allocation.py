import uuid
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, func
from app.models.fulfillment import WarehouseAllocation, FulfillmentOverrideAudit, Backorder
from app.models.warehouses import Warehouse
from app.models.inventory import InventoryStock, InventoryReservation
from app.models.quotation import Quotation, QuotationItem
from app.models.user import User
from app.schemas.inventory import SmartAllocationSummary, ManualOverrideRequest, WarehouseAllocationResponse
from app.core.exceptions import NotFoundException, BusinessRuleViolationException


async def calculate_smart_warehouse_allocation(
    session: AsyncSession,
    organization_id: uuid.UUID,
    quotation_id: uuid.UUID,
) -> SmartAllocationSummary:
    q_stmt = select(Quotation).where(Quotation.id == quotation_id, Quotation.organization_id == organization_id)
    q_res = await session.execute(q_stmt)
    quotation = q_res.scalar_one_or_none()
    if not quotation:
        raise NotFoundException(f"Quotation {quotation_id} not found")

    items_stmt = select(QuotationItem).where(QuotationItem.quotation_id == quotation_id)
    items = list((await session.execute(items_stmt)).scalars().all())

    # Delete existing draft allocations for clean calculation
    await session.execute(
        delete(WarehouseAllocation).where(
            WarehouseAllocation.organization_id == organization_id,
            WarehouseAllocation.quotation_id == quotation_id,
            WarehouseAllocation.status == "ALLOCATED"
        )
    )

    wh_stmt = select(Warehouse).where(
        Warehouse.organization_id == organization_id,
        Warehouse.is_active == True
    ).order_by(Warehouse.priority.asc())
    warehouses = list((await session.execute(wh_stmt)).scalars().all())

    allocations: List[WarehouseAllocation] = []
    total_requested = 0
    total_allocated = 0
    total_shortfall = 0

    for item in items:
        req_qty = int(item.quantity)
        total_requested += req_qty
        qty_needed = req_qty

        # Strategy 1: Check if any single warehouse can fulfill 100% of this line
        single_wh_match: Optional[Warehouse] = None
        for wh in warehouses:
            stock_stmt = select(InventoryStock).where(
                InventoryStock.organization_id == organization_id,
                InventoryStock.warehouse_id == wh.id,
                InventoryStock.product_id == item.product_id,
            )
            stock = (await session.execute(stock_stmt)).scalar_one_or_none()

            res_stmt = select(func.coalesce(func.sum(InventoryReservation.quantity), 0)).where(
                InventoryReservation.organization_id == organization_id,
                InventoryReservation.quotation_id == quotation_id,
                InventoryReservation.product_id == item.product_id,
                InventoryReservation.warehouse_id == wh.id,
                InventoryReservation.status == "ACTIVE"
            )
            reserved_for_q = int((await session.execute(res_stmt)).scalar() or 0)
            avail_stock = (stock.available_quantity + reserved_for_q) if stock else 0

            if avail_stock >= req_qty:
                single_wh_match = wh
                break

        if single_wh_match:
            alloc = WarehouseAllocation(
                organization_id=organization_id,
                quotation_id=quotation_id,
                quotation_item_id=item.id,
                warehouse_id=single_wh_match.id,
                allocated_quantity=req_qty,
                allocation_strategy="SINGLE_WAREHOUSE",
                status="ALLOCATED",
            )
            session.add(alloc)
            allocations.append(alloc)
            total_allocated += req_qty
        else:
            # Strategy 2: Multi-warehouse split across priority warehouses
            allocated_for_item = 0
            for wh in warehouses:
                if qty_needed <= 0:
                    break

                stock_stmt = select(InventoryStock).where(
                    InventoryStock.organization_id == organization_id,
                    InventoryStock.warehouse_id == wh.id,
                    InventoryStock.product_id == item.product_id,
                )
                stock = (await session.execute(stock_stmt)).scalar_one_or_none()

                res_stmt = select(func.coalesce(func.sum(InventoryReservation.quantity), 0)).where(
                    InventoryReservation.organization_id == organization_id,
                    InventoryReservation.quotation_id == quotation_id,
                    InventoryReservation.product_id == item.product_id,
                    InventoryReservation.warehouse_id == wh.id,
                    InventoryReservation.status == "ACTIVE"
                )
                reserved_for_q = int((await session.execute(res_stmt)).scalar() or 0)
                avail_stock = (stock.available_quantity + reserved_for_q) if stock else 0

                if avail_stock > 0:
                    alloc_qty = min(qty_needed, avail_stock)
                    alloc = WarehouseAllocation(
                        organization_id=organization_id,
                        quotation_id=quotation_id,
                        quotation_item_id=item.id,
                        warehouse_id=wh.id,
                        allocated_quantity=alloc_qty,
                        allocation_strategy="MINIMAL_SPLIT",
                        status="ALLOCATED",
                    )
                    session.add(alloc)
                    allocations.append(alloc)
                    allocated_for_item += alloc_qty
                    qty_needed -= alloc_qty

            total_allocated += allocated_for_item
            if qty_needed > 0:
                total_shortfall += qty_needed

    await session.commit()
    for a in allocations:
        await session.refresh(a)

    responses = [WarehouseAllocationResponse.model_validate(a) for a in allocations]
    return SmartAllocationSummary(
        quotation_id=quotation_id,
        is_fully_allocated=(total_shortfall == 0 and total_requested > 0),
        total_requested=total_requested,
        total_allocated=total_allocated,
        total_shortfall=total_shortfall,
        allocations=responses,
    )


async def apply_manual_fulfillment_override(
    session: AsyncSession,
    organization_id: uuid.UUID,
    payload: ManualOverrideRequest,
    current_user: User,
) -> WarehouseAllocation:
    """Override automatic warehouse allocation with explicit user permission check, validation, and audit trail."""
    # 1. Authorization check
    if not (current_user.is_admin or "fulfillment.override" in getattr(current_user, "permissions", [])):
        raise BusinessRuleViolationException("User lacks authorization to perform manual fulfillment override")

    # 2. Check quotation item
    item_stmt = select(QuotationItem).where(
        QuotationItem.id == payload.quotation_item_id,
        QuotationItem.quotation_id == payload.quotation_id,
    )
    item = (await session.execute(item_stmt)).scalar_one_or_none()
    if not item:
        raise NotFoundException(f"QuotationItem {payload.quotation_item_id} not found")

    # 3. Check new target warehouse
    wh_stmt = select(Warehouse).where(Warehouse.id == payload.new_warehouse_id, Warehouse.organization_id == organization_id)
    target_wh = (await session.execute(wh_stmt)).scalar_one_or_none()
    if not target_wh:
        raise NotFoundException(f"Warehouse {payload.new_warehouse_id} not found")

    # 4. Capture original allocations for audit
    existing_alloc_stmt = select(WarehouseAllocation).where(
        WarehouseAllocation.organization_id == organization_id,
        WarehouseAllocation.quotation_item_id == payload.quotation_item_id,
    )
    existing_allocs = list((await session.execute(existing_alloc_stmt)).scalars().all())
    original_data = [
        {"id": str(a.id), "warehouse_id": str(a.warehouse_id), "allocated_quantity": a.allocated_quantity, "strategy": a.allocation_strategy}
        for a in existing_allocs
    ]

    # Clear previous allocations for item
    await session.execute(
        delete(WarehouseAllocation).where(
            WarehouseAllocation.organization_id == organization_id,
            WarehouseAllocation.quotation_item_id == payload.quotation_item_id,
        )
    )

    # 5. Create new override allocation
    new_alloc = WarehouseAllocation(
        organization_id=organization_id,
        quotation_id=payload.quotation_id,
        quotation_item_id=payload.quotation_item_id,
        warehouse_id=payload.new_warehouse_id,
        allocated_quantity=payload.allocated_quantity,
        allocation_strategy="MANUAL_OVERRIDE",
        status="ALLOCATED",
    )
    session.add(new_alloc)

    # 6. Record audit entry
    audit = FulfillmentOverrideAudit(
        organization_id=organization_id,
        quotation_id=payload.quotation_id,
        quotation_item_id=payload.quotation_item_id,
        actor_id=current_user.id,
        actor_name=current_user.full_name or current_user.email,
        original_allocation={"items": original_data},
        new_allocation={"warehouse_id": str(payload.new_warehouse_id), "allocated_quantity": payload.allocated_quantity},
        reason=payload.reason,
    )
    session.add(audit)

    await session.commit()
    await session.refresh(new_alloc)
    return new_alloc
