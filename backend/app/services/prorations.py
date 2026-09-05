import uuid
from decimal import Decimal
from datetime import date
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.subscription import Subscription, BillingSchedule, SubscriptionProration
from app.models.user import User
from app.schemas.subscriptions import SubscriptionProrationRequest
from app.core.exceptions import NotFoundException, BusinessRuleViolationException


async def prorate_subscription_adjustment(
    session: AsyncSession,
    organization_id: uuid.UUID,
    subscription_id: uuid.UUID,
    payload: SubscriptionProrationRequest,
    current_user: Optional[User] = None,
) -> SubscriptionProration:
    sub_stmt = select(Subscription).where(Subscription.id == subscription_id, Subscription.organization_id == organization_id)
    subscription = (await session.execute(sub_stmt)).scalar_one_or_none()
    if not subscription:
        raise NotFoundException(f"Subscription {subscription_id} not found")

    if subscription.status not in ["ACTIVE", "TRIAL"]:
        raise BusinessRuleViolationException(f"Cannot perform proration adjustment on subscription in status '{subscription.status}'.")

    eff_date = payload.effective_date or date.today()

    # Find current active billing schedule period
    sched_stmt = select(BillingSchedule).where(
        BillingSchedule.organization_id == organization_id,
        BillingSchedule.subscription_id == subscription_id,
        BillingSchedule.billing_period_start <= eff_date,
        BillingSchedule.billing_period_end >= eff_date,
    ).order_by(BillingSchedule.billing_period_start.desc())
    current_sched = (await session.execute(sched_stmt)).scalar_one_or_none()

    if current_sched:
        period_start = current_sched.billing_period_start
        period_end = current_sched.billing_period_end
    else:
        period_start = subscription.start_date
        period_end = subscription.next_billing_date

    total_days = (period_end - period_start).days
    if total_days <= 0:
        total_days = 30

    remaining_days = (period_end - eff_date).days
    if remaining_days < 0:
        remaining_days = 0

    old_qty = Decimal(str(subscription.quantity))
    old_price = Decimal(str(subscription.unit_price))
    old_period_charge = old_qty * old_price

    new_qty = Decimal(str(payload.new_quantity))
    new_price = Decimal(str(payload.new_unit_price))
    new_period_charge = new_qty * new_price

    charge_delta = new_period_charge - old_period_charge
    day_fraction = Decimal(str(remaining_days)) / Decimal(str(total_days))
    prorated_amount = (charge_delta * day_fraction).quantize(Decimal("0.01"))

    actor_name = current_user.full_name or current_user.email if current_user else "System"

    proration = SubscriptionProration(
        organization_id=organization_id,
        subscription_id=subscription_id,
        old_quantity=old_qty,
        new_quantity=new_qty,
        old_unit_price=old_price,
        new_unit_price=new_price,
        billing_period_start=period_start,
        billing_period_end=period_end,
        effective_date=eff_date,
        total_period_days=total_days,
        remaining_days=remaining_days,
        prorated_amount=prorated_amount,
        actor_id=current_user.id if current_user else None,
        actor_name=actor_name,
        notes=payload.notes,
    )
    session.add(proration)

    # Update subscription to new parameters
    subscription.quantity = new_qty
    subscription.unit_price = new_price

    await session.commit()
    await session.refresh(proration)
    return proration


async def list_prorations_for_subscription(
    session: AsyncSession,
    organization_id: uuid.UUID,
    subscription_id: uuid.UUID,
) -> List[SubscriptionProration]:
    stmt = select(SubscriptionProration).where(
        SubscriptionProration.organization_id == organization_id,
        SubscriptionProration.subscription_id == subscription_id,
    ).order_by(SubscriptionProration.created_at.desc())
    return list((await session.execute(stmt)).scalars().all())
