import uuid
from typing import List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_, or_, func
from app.models.warehouses import Warehouse, ProductVariant
from app.models.inventory import InventoryStock, InventoryMovement
from app.models.product import Product
from app.models.quotation import Quotation, QuotationItem
from app.schemas.inventory import (
    WarehouseCreate,
    ProductVariantCreate,
    StockAdjustmentRequest,
    StockReceiptRequest,
    LineAvailabilityItem,
    QuotationAvailabilitySummary,
)
from app.core.exceptions import NotFoundException, BusinessRuleViolationException


# --- Phase 36 Services: Warehouse, Variants & Stock Transactions ---

async def create_warehouse(session: AsyncSession, organization_id: uuid.UUID, payload: WarehouseCreate) -> Warehouse:
    """Create a new Warehouse record for an Organization."""
    existing = await session.execute(
        select(Warehouse).where(
            Warehouse.organization_id == organization_id,
            Warehouse.code == payload.code.upper()
        )
    )
    if existing.scalar_one_or_none():
        raise BusinessRuleViolationException(f"Warehouse code '{payload.code.upper()}' already exists in organization")

    warehouse = Warehouse(
        organization_id=organization_id,
        code=payload.code.upper(),
        name=payload.name,
        address=payload.address,
        priority=payload.priority,
        is_active=payload.is_active,
    )
    session.add(warehouse)
    await session.commit()
    await session.refresh(warehouse)
    return warehouse


async def get_warehouses(session: AsyncSession, organization_id: uuid.UUID) -> List[Warehouse]:
    """Retrieve all warehouses for an Organization."""
    stmt = select(Warehouse).where(Warehouse.organization_id == organization_id).order_by(Warehouse.priority.asc(), Warehouse.name.asc())
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def create_product_variant(session: AsyncSession, organization_id: uuid.UUID, payload: ProductVariantCreate) -> ProductVariant:
    """Create a product variant."""
    # Verify product exists in organization
    prod_stmt = select(Product).where(Product.id == payload.product_id, Product.organization_id == organization_id)
    prod_res = await session.execute(prod_stmt)
    if not prod_res.scalar_one_or_none():
        raise NotFoundException(f"Product {payload.product_id} not found")

    variant = ProductVariant(
        organization_id=organization_id,
        product_id=payload.product_id,
        sku=payload.sku.upper(),
        name=payload.name,
        unit_price_override=payload.unit_price_override,
        is_active=payload.is_active,
    )
    session.add(variant)
    await session.commit()
    await session.refresh(variant)
    return variant


async def record_stock_receipt(
    session: AsyncSession,
    organization_id: uuid.UUID,
    payload: StockReceiptRequest,
    actor_id: Optional[uuid.UUID] = None,
    actor_name: Optional[str] = None,
) -> InventoryStock:
    """Record receipt of physical stock into a warehouse location."""
    stmt = select(InventoryStock).where(
        InventoryStock.organization_id == organization_id,
        InventoryStock.warehouse_id == payload.warehouse_id,
        InventoryStock.product_id == payload.product_id,
        InventoryStock.variant_id == payload.variant_id,
    )
    result = await session.execute(stmt)
    stock = result.scalar_one_or_none()

    if not stock:
        stock = InventoryStock(
            organization_id=organization_id,
            warehouse_id=payload.warehouse_id,
            product_id=payload.product_id,
            variant_id=payload.variant_id,
            location_code="MAIN",
            on_hand_quantity=payload.quantity,
            reserved_quantity=0,
            available_quantity=payload.quantity,
        )
        session.add(stock)
    else:
        stock.on_hand_quantity += payload.quantity
        stock.available_quantity = stock.on_hand_quantity - stock.reserved_quantity

    movement = InventoryMovement(
        organization_id=organization_id,
        warehouse_id=payload.warehouse_id,
        product_id=payload.product_id,
        variant_id=payload.variant_id,
        quantity=payload.quantity,
        movement_type="RECEIPT",
        reference_type="MANUAL",
        actor_id=actor_id,
        actor_name=actor_name,
        notes=payload.notes or "Manual Stock Receipt",
    )
    session.add(movement)

    await session.commit()
    await session.refresh(stock)
    return stock


async def get_inventory_stocks(
    session: AsyncSession,
    organization_id: uuid.UUID,
    warehouse_id: Optional[uuid.UUID] = None,
    product_id: Optional[uuid.UUID] = None,
) -> List[InventoryStock]:
    """Retrieve inventory stock records."""
    stmt = select(InventoryStock).where(InventoryStock.organization_id == organization_id)
    if warehouse_id:
        stmt = stmt.where(InventoryStock.warehouse_id == warehouse_id)
    if product_id:
        stmt = stmt.where(InventoryStock.product_id == product_id)

    result = await session.execute(stmt)
    return list(result.scalars().all())


async def get_inventory_movements(
    session: AsyncSession,
    organization_id: uuid.UUID,
    warehouse_id: Optional[uuid.UUID] = None,
    product_id: Optional[uuid.UUID] = None,
) -> List[InventoryMovement]:
    """Retrieve inventory stock movement ledger records."""
    stmt = select(InventoryMovement).where(InventoryMovement.organization_id == organization_id).order_by(InventoryMovement.created_at.desc())
    if warehouse_id:
        stmt = stmt.where(InventoryMovement.warehouse_id == warehouse_id)
    if product_id:
        stmt = stmt.where(InventoryMovement.product_id == product_id)

    result = await session.execute(stmt)
    return list(result.scalars().all())



# --- Phase 37 Services: Authoritative Stock Availability Calculation ---

async def calculate_quotation_availability(
    session: AsyncSession,
    organization_id: uuid.UUID,
    quotation_id: uuid.UUID,
) -> QuotationAvailabilitySummary:
    """Calculate authoritative stock availability for each item in a quotation."""
    # 1. Fetch quotation
    q_stmt = select(Quotation).where(Quotation.id == quotation_id, Quotation.organization_id == organization_id)
    q_res = await session.execute(q_stmt)
    quotation = q_res.scalar_one_or_none()
    if not quotation:
        raise NotFoundException(f"Quotation {quotation_id} not found")

    # 2. Fetch items
    items_stmt = select(QuotationItem).where(QuotationItem.quotation_id == quotation_id)
    items = list((await session.execute(items_stmt)).scalars().all())

    line_availabilities: List[LineAvailabilityItem] = []
    total_requested = 0
    total_available = 0
    total_shortfall = 0

    product_ids = list({item.product_id for item in items})
    stock_map = {}
    prod_map = {}

    if product_ids:
        stock_stmt = (
            select(
                InventoryStock.product_id,
                func.coalesce(func.sum(InventoryStock.on_hand_quantity), 0).label("on_hand"),
                func.coalesce(func.sum(InventoryStock.reserved_quantity), 0).label("reserved"),
                func.coalesce(func.sum(InventoryStock.available_quantity), 0).label("available"),
            )
            .where(
                InventoryStock.organization_id == organization_id,
                InventoryStock.product_id.in_(product_ids),
            )
            .group_by(InventoryStock.product_id)
        )
        stock_rows = (await session.execute(stock_stmt)).all()
        for r in stock_rows:
            stock_map[r.product_id] = {
                "on_hand": int(r.on_hand),
                "reserved": int(r.reserved),
                "available": int(r.available),
            }

        prod_stmt = select(Product.id, Product.name).where(Product.id.in_(product_ids))
        prod_rows = (await session.execute(prod_stmt)).all()
        for pr in prod_rows:
            prod_map[pr.id] = pr.name

    for item in items:
        stk = stock_map.get(item.product_id, {"on_hand": 0, "reserved": 0, "available": 0})
        on_hand = stk["on_hand"]
        reserved = stk["reserved"]
        available = stk["available"]

        req_qty = item.quantity
        shortfall = max(0, req_qty - available)

        if available >= req_qty:
            status = "AVAILABLE"
        elif available > 0:
            status = "PARTIALLY_AVAILABLE"
        else:
            status = "OUT_OF_STOCK"

        prod_name = prod_map.get(item.product_id, "Product")

        line_availabilities.append(
            LineAvailabilityItem(
                quotation_item_id=item.id,
                product_id=item.product_id,
                variant_id=None,
                product_name=prod_name,
                requested_quantity=req_qty,
                on_hand_quantity=on_hand,
                reserved_quantity=reserved,
                available_quantity=available,
                shortfall_quantity=shortfall,
                status=status,
            )
        )

        total_requested += req_qty
        total_available += min(req_qty, available)
        total_shortfall += shortfall

    if total_shortfall == 0 and total_requested > 0:
        overall_status = "AVAILABLE"
    elif total_available > 0:
        overall_status = "PARTIALLY_AVAILABLE"
    else:
        overall_status = "OUT_OF_STOCK"

    return QuotationAvailabilitySummary(
        quotation_id=quotation_id,
        overall_status=overall_status,
        total_requested=total_requested,
        total_available=total_available,
        total_shortfall=total_shortfall,
        line_availabilities=line_availabilities,
    )
