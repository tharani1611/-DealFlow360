import uuid
from decimal import Decimal
from datetime import date
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.payment import Payment
from app.models.invoice import Invoice
from app.models.user import User
from app.schemas.payments import PaymentCreateRequest
from app.core.exceptions import NotFoundException, BusinessRuleViolationException


async def generate_payment_reference(session: AsyncSession, organization_id: uuid.UUID) -> str:
    stmt = (
        select(Payment.payment_reference)
        .where(Payment.organization_id == organization_id)
        .order_by(Payment.created_at.desc(), Payment.payment_reference.desc())
        .limit(20)
    )
    result = await session.execute(stmt)
    references = result.scalars().all()

    max_num = 0
    for ref in references:
        if ref and ref.startswith("PAY-"):
            try:
                num = int(ref.replace("PAY-", "").strip())
                if num > max_num:
                    max_num = num
            except ValueError:
                continue

    return f"PAY-{max_num + 1:06d}"


async def record_payment(
    session: AsyncSession,
    organization_id: uuid.UUID,
    payload: PaymentCreateRequest,
    current_user: Optional[User] = None,
) -> Payment:
    # 1. Fetch & validate invoice with row-level lock for concurrency safety
    inv_stmt = select(Invoice).where(
        Invoice.id == payload.invoice_id,
        Invoice.organization_id == organization_id
    ).with_for_update()
    invoice = (await session.execute(inv_stmt)).scalar_one_or_none()
    if not invoice:
        raise NotFoundException(f"Invoice {payload.invoice_id} not found")

    if invoice.status in ["DRAFT", "VOID"]:
        raise BusinessRuleViolationException(f"Payments cannot be recorded against an invoice in status '{invoice.status}'. Must be ISSUED, PARTIALLY_PAID, or OVERDUE.")

    pay_amount = Decimal(str(payload.amount))
    if pay_amount <= Decimal("0.00"):
        raise BusinessRuleViolationException("Payment amount must be greater than zero.")

    if pay_amount > invoice.amount_due:
        raise BusinessRuleViolationException(f"Payment amount ({pay_amount}) exceeds remaining invoice balance due ({invoice.amount_due}).")

    ref_num = await generate_payment_reference(session, organization_id)
    pay_date = payload.payment_date or date.today()

    payment = Payment(
        organization_id=organization_id,
        payment_reference=ref_num,
        invoice_id=invoice.id,
        customer_id=invoice.customer_id,
        payment_date=pay_date,
        amount=pay_amount,
        method=payload.method,
        status="COMPLETED",
        notes=payload.notes,
        created_by_user_id=current_user.id if current_user else None,
    )
    session.add(payment)

    # 2. Update invoice balance and status
    invoice.amount_paid += pay_amount
    invoice.amount_due = invoice.total - invoice.amount_paid

    if invoice.amount_due == Decimal("0.00"):
        invoice.status = "PAID"
    elif invoice.amount_paid > Decimal("0.00"):
        invoice.status = "PARTIALLY_PAID"

    await session.commit()
    await session.refresh(payment)
    return payment


async def get_payment(session: AsyncSession, organization_id: uuid.UUID, payment_id: uuid.UUID) -> Payment:
    stmt = select(Payment).where(Payment.id == payment_id, Payment.organization_id == organization_id)
    payment = (await session.execute(stmt)).scalar_one_or_none()
    if not payment:
        raise NotFoundException(f"Payment {payment_id} not found")
    return payment


async def list_payments_for_invoice(session: AsyncSession, organization_id: uuid.UUID, invoice_id: uuid.UUID) -> List[Payment]:
    stmt = select(Payment).where(Payment.organization_id == organization_id, Payment.invoice_id == invoice_id).order_by(Payment.created_at.desc())
    return list((await session.execute(stmt)).scalars().all())


async def list_payments_for_customer(session: AsyncSession, organization_id: uuid.UUID, customer_id: uuid.UUID) -> List[Payment]:
    stmt = select(Payment).where(Payment.organization_id == organization_id, Payment.customer_id == customer_id).order_by(Payment.created_at.desc())
    return list((await session.execute(stmt)).scalars().all())
