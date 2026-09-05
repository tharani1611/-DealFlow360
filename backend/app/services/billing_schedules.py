import uuid
from decimal import Decimal
from datetime import date, timedelta
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.subscription import Subscription, BillingSchedule
from app.models.invoice import Invoice, InvoiceItem
from app.services.invoices import generate_invoice_number, calculate_invoice_totals, get_invoice
from app.services.subscriptions import calculate_next_billing_date
from app.core.exceptions import NotFoundException, BusinessRuleViolationException


async def generate_due_billing_schedules(
    session: AsyncSession,
    organization_id: uuid.UUID,
    as_of_date: Optional[date] = None,
) -> List[BillingSchedule]:
    target_date = as_of_date or date.today()
    stmt = select(Subscription).where(
        Subscription.organization_id == organization_id,
        Subscription.status == "ACTIVE",
        Subscription.next_billing_date <= target_date,
    )
    active_subs = list((await session.execute(stmt)).scalars().all())
    generated_schedules: List[BillingSchedule] = []

    for sub in active_subs:
        period_start = sub.next_billing_date
        period_end = calculate_next_billing_date(period_start, sub.billing_interval)

        # Idempotency check: ensure schedule doesn't already exist for this exact period
        exist_stmt = select(BillingSchedule).where(
            BillingSchedule.organization_id == organization_id,
            BillingSchedule.subscription_id == sub.id,
            BillingSchedule.billing_period_start == period_start,
            BillingSchedule.billing_period_end == period_end,
        )
        existing = (await session.execute(exist_stmt)).scalar_one_or_none()
        if existing:
            generated_schedules.append(existing)
            continue

        sched_amount = sub.quantity * sub.unit_price
        schedule = BillingSchedule(
            organization_id=organization_id,
            subscription_id=sub.id,
            billing_period_start=period_start,
            billing_period_end=period_end,
            billing_date=period_start,
            amount=sched_amount,
            status="SCHEDULED",
        )
        session.add(schedule)
        sub.next_billing_date = period_end
        generated_schedules.append(schedule)

    await session.commit()
    return generated_schedules


async def execute_billing_schedule_invoice(
    session: AsyncSession,
    organization_id: uuid.UUID,
    schedule_id: uuid.UUID,
) -> Invoice:
    sched_stmt = select(BillingSchedule).where(BillingSchedule.id == schedule_id, BillingSchedule.organization_id == organization_id)
    schedule = (await session.execute(sched_stmt)).scalar_one_or_none()
    if not schedule:
        raise NotFoundException(f"BillingSchedule {schedule_id} not found")

    if schedule.status in ["INVOICED", "PAID", "CANCELLED"]:
        if schedule.invoice_id:
            inv_stmt = select(Invoice).where(Invoice.id == schedule.invoice_id, Invoice.organization_id == organization_id)
            inv = (await session.execute(inv_stmt)).scalar_one_or_none()
            if inv:
                return inv
        raise BusinessRuleViolationException(f"Billing schedule is in status '{schedule.status}' and cannot be invoiced again.")

    sub_stmt = select(Subscription).where(Subscription.id == schedule.subscription_id, Subscription.organization_id == organization_id)
    sub = (await session.execute(sub_stmt)).scalar_one_or_none()
    if not sub:
        raise NotFoundException(f"Subscription {schedule.subscription_id} not found")

    if sub.status not in ["ACTIVE", "TRIAL"]:
        raise BusinessRuleViolationException(f"Cannot generate billing invoice for subscription in status '{sub.status}'.")

    invoice_number = await generate_invoice_number(session, organization_id)
    inv_date = date.today()
    due_dt = inv_date + timedelta(days=14)

    invoice = Invoice(
        organization_id=organization_id,
        invoice_number=invoice_number,
        customer_id=sub.customer_id,
        quotation_id=sub.quotation_id,
        currency="USD",
        invoice_date=inv_date,
        due_date=due_dt,
        status="DRAFT",
    )
    session.add(invoice)
    await session.flush()

    desc = f"Recurring Subscription: {sub.plan_name} ({schedule.billing_period_start} to {schedule.billing_period_end})"
    item = InvoiceItem(
        organization_id=organization_id,
        invoice_id=invoice.id,
        product_id=sub.product_id,
        product_variant_id=sub.variant_id,
        quotation_item_id=sub.quotation_item_id,
        description=desc,
        quantity=sub.quantity,
        unit_price=sub.unit_price,
        discount_amount=Decimal("0.00"),
        tax_amount=Decimal("0.00"),
        billing_type="RECURRING",
    )
    session.add(item)
    await calculate_invoice_totals(invoice, [item])

    schedule.status = "INVOICED"
    schedule.invoice_id = invoice.id

    await session.commit()
    return await get_invoice(session, organization_id, invoice.id)


async def list_schedules_for_subscription(
    session: AsyncSession,
    organization_id: uuid.UUID,
    subscription_id: uuid.UUID,
) -> List[BillingSchedule]:
    stmt = select(BillingSchedule).where(
        BillingSchedule.organization_id == organization_id,
        BillingSchedule.subscription_id == subscription_id,
    ).order_by(BillingSchedule.billing_period_start.asc())
    return list((await session.execute(stmt)).scalars().all())
