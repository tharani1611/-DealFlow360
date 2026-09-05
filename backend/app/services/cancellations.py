import uuid
from datetime import date
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app.models.subscription import Subscription, BillingSchedule, SubscriptionCancellation
from app.models.user import User
from app.schemas.subscriptions import SubscriptionCancellationRequest
from app.core.exceptions import NotFoundException, BusinessRuleViolationException


async def cancel_subscription(
    session: AsyncSession,
    organization_id: uuid.UUID,
    subscription_id: uuid.UUID,
    payload: SubscriptionCancellationRequest,
    current_user: Optional[User] = None,
) -> SubscriptionCancellation:
    sub_stmt = select(Subscription).where(Subscription.id == subscription_id, Subscription.organization_id == organization_id)
    subscription = (await session.execute(sub_stmt)).scalar_one_or_none()
    if not subscription:
        raise NotFoundException(f"Subscription {subscription_id} not found")

    if subscription.status in ["CANCELLED", "EXPIRED"]:
        raise BusinessRuleViolationException(f"Subscription is already in status '{subscription.status}'.")

    today = date.today()
    eff_date = today if payload.cancellation_type == "IMMEDIATE" else subscription.next_billing_date

    cancellation = SubscriptionCancellation(
        organization_id=organization_id,
        subscription_id=subscription_id,
        cancellation_type=payload.cancellation_type,
        reason=payload.reason,
        requested_by_user_id=current_user.id if current_user else None,
        effective_date=eff_date,
        notes=payload.notes,
    )
    session.add(cancellation)

    if payload.cancellation_type == "IMMEDIATE":
        subscription.status = "CANCELLED"
        subscription.end_date = today

        # Cancel all future scheduled/due billing entries
        await session.execute(
            update(BillingSchedule)
            .where(
                BillingSchedule.organization_id == organization_id,
                BillingSchedule.subscription_id == subscription_id,
                BillingSchedule.status.in_(["SCHEDULED", "DUE"]),
            )
            .values(status="CANCELLED")
        )
    else:  # END_OF_PERIOD
        subscription.end_date = subscription.next_billing_date
        # Cancel schedules strictly past effective date
        await session.execute(
            update(BillingSchedule)
            .where(
                BillingSchedule.organization_id == organization_id,
                BillingSchedule.subscription_id == subscription_id,
                BillingSchedule.billing_period_start >= eff_date,
                BillingSchedule.status.in_(["SCHEDULED", "DUE"]),
            )
            .values(status="CANCELLED")
        )

    await session.commit()
    await session.refresh(cancellation)
    return cancellation


async def get_cancellation_audit(
    session: AsyncSession,
    organization_id: uuid.UUID,
    subscription_id: uuid.UUID,
) -> Optional[SubscriptionCancellation]:
    stmt = select(SubscriptionCancellation).where(
        SubscriptionCancellation.organization_id == organization_id,
        SubscriptionCancellation.subscription_id == subscription_id,
    ).order_by(SubscriptionCancellation.created_at.desc())
    return (await session.execute(stmt)).scalar_one_or_none()
