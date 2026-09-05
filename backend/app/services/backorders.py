import uuid
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func
from app.models.fulfillment import Backorder
from app.models.quotation import Quotation, QuotationItem
from app.models.product import Product
from app.schemas.inventory import BackorderConsolidationSummary, BackorderResponse
from app.core.exceptions import NotFoundException, BusinessRuleViolationException


async def create_backorders_for_quotation_shortfall(
    session: AsyncSession,
    organization_id: uuid.UUID,
    quotation_id: uuid.UUID,
    shortfall_dict: dict,  # {quotation_item_id: shortfall_quantity}
) -> List[Backorder]:
    """Create idempotent backorders for unfulfilled item shortfalls."""
    q_stmt = select(Quotation).where(Quotation.id == quotation_id, Quotation.organization_id == organization_id)
    q_res = await session.execute(q_stmt)
    quotation = q_res.scalar_one_or_none()
    if not quotation:
        raise NotFoundException(f"Quotation {quotation_id} not found")

    backorders: List[Backorder] = []

    for item_id, shortfall in shortfall_dict.items():
        if shortfall <= 0:
            continue

        # Check existing backorder to avoid duplicate creation
        existing_stmt = select(Backorder).where(
            Backorder.organization_id == organization_id,
            Backorder.quotation_id == quotation_id,
            Backorder.quotation_item_id == item_id,
            Backorder.status == "OPEN",
        )
        existing = (await session.execute(existing_stmt)).scalar_one_or_none()
        if existing:
            existing.remaining_quantity = shortfall
            backorders.append(existing)
            continue

        item_stmt = select(QuotationItem).where(QuotationItem.id == item_id)
        item = (await session.execute(item_stmt)).scalar_one_or_none()
        if not item:
            continue

        bo_num = f"BO-{quotation.quotation_number.replace('QT-', '')}-{uuid.uuid4().hex[:4].upper()}"
        bo = Backorder(
            organization_id=organization_id,
            backorder_number=bo_num,
            quotation_id=quotation_id,
            quotation_item_id=item_id,
            customer_id=quotation.customer_id,
            product_id=item.product_id,
            variant_id=None,
            requested_quantity=item.quantity,
            fulfilled_quantity=item.quantity - shortfall,
            remaining_quantity=shortfall,
            status="OPEN",
        )
        session.add(bo)
        backorders.append(bo)

    await session.commit()
    for b in backorders:
        await session.refresh(b)
    return backorders


async def get_customer_backorder_consolidation(
    session: AsyncSession,
    organization_id: uuid.UUID,
    customer_id: uuid.UUID,
) -> BackorderConsolidationSummary:
    """Consolidate open backorders for a given customer across all active quotations."""
    stmt = select(Backorder).where(
        Backorder.organization_id == organization_id,
        Backorder.customer_id == customer_id,
        Backorder.status.in_(["OPEN", "PARTIALLY_FULFILLED"]),
    ).order_by(Backorder.created_at.asc())

    backorders = list((await session.execute(stmt)).scalars().all())
    total_remaining = sum(b.remaining_quantity for b in backorders)

    responses = [BackorderResponse.model_validate(b) for b in backorders]
    return BackorderConsolidationSummary(
        customer_id=customer_id,
        total_open_backorders=len(backorders),
        total_remaining_quantity=total_remaining,
        backorders=responses,
    )


async def get_organization_backorders(
    session: AsyncSession,
    organization_id: uuid.UUID,
    status: Optional[str] = None,
) -> List[Backorder]:
    """List backorders for an organization."""
    stmt = select(Backorder).where(Backorder.organization_id == organization_id)
    if status:
        stmt = stmt.where(Backorder.status == status.upper())
    result = await session.execute(stmt)
    return list(result.scalars().all())
