import uuid
from datetime import date, timedelta
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app.models.fulfillment import DeliveryPromise, Shipment, Backorder
from app.models.quotation import Quotation
from app.core.exceptions import NotFoundException


async def calculate_or_update_delivery_promise(
    session: AsyncSession,
    organization_id: uuid.UUID,
    quotation_id: uuid.UUID,
    lead_time_days: int = 7,
) -> DeliveryPromise:
    """Calculate promised vs expected delivery dates and track slippage."""
    # Check if delivery promise already exists
    stmt = select(DeliveryPromise).where(
        DeliveryPromise.organization_id == organization_id,
        DeliveryPromise.quotation_id == quotation_id,
    )
    promise = (await session.execute(stmt)).scalar_one_or_none()

    q_stmt = select(Quotation).where(Quotation.id == quotation_id, Quotation.organization_id == organization_id)
    quotation = (await session.execute(q_stmt)).scalar_one_or_none()
    if not quotation:
        raise NotFoundException(f"Quotation {quotation_id} not found")

    today = date.today()
    promised_date = quotation.created_at.date() + timedelta(days=lead_time_days)
    expected_date = promised_date

    # Check shipment status for updated expected/actual dates
    shp_stmt = select(Shipment).where(
        Shipment.organization_id == organization_id,
        Shipment.quotation_id == quotation_id,
    ).order_by(Shipment.created_at.desc())
    shipment = (await session.execute(shp_stmt)).scalars().first()

    actual_date = None
    if shipment:
        if shipment.expected_delivery_date:
            expected_date = shipment.expected_delivery_date
        if shipment.actual_delivery_date:
            actual_date = shipment.actual_delivery_date

    # Check backorders
    bo_stmt = select(Backorder).where(
        Backorder.organization_id == organization_id,
        Backorder.quotation_id == quotation_id,
        Backorder.status == "OPEN",
    )
    open_backorders = list((await session.execute(bo_stmt)).scalars().all())

    if open_backorders and not actual_date:
        expected_date = today + timedelta(days=14)  # Delayed expected delivery due to backorder

    # Calculate slippage
    ref_date = actual_date or expected_date
    slippage = (ref_date - promised_date).days

    if actual_date:
        status = "DELIVERED"
    elif slippage > 3:
        status = "DELAYED"
    elif slippage > 0 or open_backorders:
        status = "AT_RISK"
    else:
        status = "ON_TRACK"

    if not promise:
        promise = DeliveryPromise(
            organization_id=organization_id,
            quotation_id=quotation_id,
            shipment_id=shipment.id if shipment else None,
            promised_date=promised_date,
            expected_date=expected_date,
            actual_date=actual_date,
            status=status,
            slippage_days=max(0, slippage),
            notes="Delivery promise calculated from commercial fulfillment status",
        )
        session.add(promise)
    else:
        promise.expected_date = expected_date
        promise.actual_date = actual_date
        promise.status = status
        promise.slippage_days = max(0, slippage)
        if shipment:
            promise.shipment_id = shipment.id

    await session.commit()
    await session.refresh(promise)
    return promise


async def get_delivery_promises_for_organization(
    session: AsyncSession,
    organization_id: uuid.UUID,
    status: Optional[str] = None,
) -> List[DeliveryPromise]:
    """Retrieve delivery promises for organization."""
    stmt = select(DeliveryPromise).where(DeliveryPromise.organization_id == organization_id)
    if status:
        stmt = stmt.where(DeliveryPromise.status == status.upper())
    result = await session.execute(stmt)
    return list(result.scalars().all())
