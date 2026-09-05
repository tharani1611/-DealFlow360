import uuid
from decimal import Decimal
from datetime import date, timedelta
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.subscription import Subscription, BillingSchedule
from app.models.quotation import Quotation, QuotationItem
from app.models.product import Product
from app.models.customer import Customer
from app.schemas.subscriptions import SubscriptionCreateRequest, SubscriptionUpdateRequest
from app.core.exceptions import NotFoundException, BusinessRuleViolationException


def calculate_next_billing_date(start: date, interval: str) -> date:
    """Calculates the end of the billing period/next billing date based on calendar intervals."""
    if interval == "YEARLY":
        try:
            return start.replace(year=start.year + 1)
        except ValueError:  # February 29 leap year fallback
            return start.replace(year=start.year + 1, day=28)
    elif interval == "QUARTERLY":
        month = start.month + 3
        year = start.year + (month - 1) // 12
        month = ((month - 1) % 12) + 1
        day = min(start.day, [31, 29 if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0) else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month - 1])
        return date(year, month, day)
    else:  # MONTHLY (default)
        month = start.month + 1
        year = start.year + (month - 1) // 12
        month = ((month - 1) % 12) + 1
        day = min(start.day, [31, 29 if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0) else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month - 1])
        return date(year, month, day)


async def generate_subscription_number(session: AsyncSession, organization_id: uuid.UUID) -> str:
    stmt = select(func.count(Subscription.id)).where(Subscription.organization_id == organization_id)
    count = int((await session.execute(stmt)).scalar() or 0) + 1
    return f"SUB-{count:06d}"


from sqlalchemy.orm import selectinload


async def create_subscription(
    session: AsyncSession,
    organization_id: uuid.UUID,
    payload: SubscriptionCreateRequest,
) -> Subscription:
    c_stmt = select(Customer).where(Customer.id == payload.customer_id, Customer.organization_id == organization_id)
    customer = (await session.execute(c_stmt)).scalar_one_or_none()
    if not customer:
        raise NotFoundException(f"Customer {payload.customer_id} not found")

    p_stmt = select(Product).where(Product.id == payload.product_id, Product.organization_id == organization_id)
    product = (await session.execute(p_stmt)).scalar_one_or_none()
    if not product:
        raise NotFoundException(f"Product {payload.product_id} not found")

    sub_number = await generate_subscription_number(session, organization_id)
    st_date = payload.start_date or date.today()
    next_bill = calculate_next_billing_date(st_date, payload.billing_interval)

    subscription = Subscription(
        organization_id=organization_id,
        subscription_number=sub_number,
        customer_id=payload.customer_id,
        quotation_id=payload.quotation_id,
        quotation_item_id=payload.quotation_item_id,
        product_id=payload.product_id,
        variant_id=payload.variant_id,
        plan_name=payload.plan_name,
        quantity=payload.quantity,
        unit_price=payload.unit_price,
        billing_interval=payload.billing_interval,
        start_date=st_date,
        next_billing_date=next_bill,
        status="ACTIVE",
    )
    session.add(subscription)
    await session.flush()

    # Automatically generate initial billing schedule
    sched_amount = subscription.quantity * subscription.unit_price
    schedule = BillingSchedule(
        organization_id=organization_id,
        subscription_id=subscription.id,
        billing_period_start=st_date,
        billing_period_end=next_bill,
        billing_date=st_date,
        amount=sched_amount,
        status="SCHEDULED",
    )
    session.add(schedule)

    await session.commit()
    return await get_subscription(session, organization_id, subscription.id)


async def create_subscriptions_from_quotation(
    session: AsyncSession,
    organization_id: uuid.UUID,
    quotation_id: uuid.UUID,
) -> List[Subscription]:
    q_stmt = select(Quotation).where(Quotation.id == quotation_id, Quotation.organization_id == organization_id)
    quotation = (await session.execute(q_stmt)).scalar_one_or_none()
    if not quotation:
        raise NotFoundException(f"Quotation {quotation_id} not found")

    if quotation.status in ["draft", "rejected", "cancelled", "expired"]:
        raise BusinessRuleViolationException(f"Cannot create subscriptions for quotation in status '{quotation.status}'.")

    items_stmt = select(QuotationItem).where(QuotationItem.quotation_id == quotation_id)
    items = list((await session.execute(items_stmt)).scalars().all())

    created_subs: List[Subscription] = []

    for item in items:
        # Check if item is recurring or subscription plan (name contains Subscription/Plan or SKU contains SUB)
        is_recurring = "sub" in (item.sku or "").lower() or "subscription" in item.product_name.lower() or "plan" in item.product_name.lower()
        if not is_recurring:
            continue

        # Prevent duplicate subscription creation for same quotation item
        exist_stmt = select(Subscription).where(
            Subscription.organization_id == organization_id,
            Subscription.quotation_item_id == item.id,
        )
        existing = (await session.execute(exist_stmt)).scalar_one_or_none()
        if existing:
            created_subs.append(await get_subscription(session, organization_id, existing.id))
            continue

        sub_req = SubscriptionCreateRequest(
            customer_id=quotation.customer_id,
            product_id=item.product_id,
            variant_id=item.product_variant_id,
            quotation_id=quotation.id,
            quotation_item_id=item.id,
            plan_name=item.product_name,
            quantity=item.quantity,
            unit_price=item.unit_price,
            billing_interval="MONTHLY",
            start_date=date.today(),
        )
        sub = await create_subscription(session, organization_id, sub_req)
        created_subs.append(sub)

    return created_subs


async def update_subscription_status(
    session: AsyncSession,
    organization_id: uuid.UUID,
    subscription_id: uuid.UUID,
    new_status: str,
) -> Subscription:
    sub_stmt = select(Subscription).where(Subscription.id == subscription_id, Subscription.organization_id == organization_id)
    subscription = (await session.execute(sub_stmt)).scalar_one_or_none()
    if not subscription:
        raise NotFoundException(f"Subscription {subscription_id} not found")

    valid_statuses = ["TRIAL", "ACTIVE", "PAUSED", "CANCELLED", "EXPIRED"]
    if new_status not in valid_statuses:
        raise BusinessRuleViolationException(f"Invalid subscription status '{new_status}'. Allowed: {valid_statuses}")

    subscription.status = new_status
    await session.commit()
    return await get_subscription(session, organization_id, subscription_id)


async def get_subscription(session: AsyncSession, organization_id: uuid.UUID, subscription_id: uuid.UUID) -> Subscription:
    stmt = select(Subscription).options(selectinload(Subscription.schedules)).where(Subscription.id == subscription_id, Subscription.organization_id == organization_id)
    sub = (await session.execute(stmt)).scalar_one_or_none()
    if not sub:
        raise NotFoundException(f"Subscription {subscription_id} not found")
    return sub


async def list_subscriptions(session: AsyncSession, organization_id: uuid.UUID, customer_id: Optional[uuid.UUID] = None) -> List[Subscription]:
    stmt = select(Subscription).options(selectinload(Subscription.schedules)).where(Subscription.organization_id == organization_id)
    if customer_id:
        stmt = stmt.where(Subscription.customer_id == customer_id)
    stmt = stmt.order_by(Subscription.created_at.desc())
    return list((await session.execute(stmt)).scalars().all())
