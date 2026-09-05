import uuid
from decimal import Decimal
from datetime import date
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.credit_note import CreditNote, CreditNoteItem, PaymentRefund
from app.models.invoice import Invoice
from app.models.payment import Payment
from app.models.user import User
from app.schemas.credit_notes import CreditNoteCreateRequest, PaymentRefundCreateRequest
from app.core.exceptions import NotFoundException, BusinessRuleViolationException


async def generate_credit_note_number(session: AsyncSession, organization_id: uuid.UUID) -> str:
    stmt = (
        select(CreditNote.credit_note_number)
        .where(CreditNote.organization_id == organization_id)
        .order_by(CreditNote.created_at.desc(), CreditNote.credit_note_number.desc())
        .limit(20)
    )
    references = (await session.execute(stmt)).scalars().all()
    max_num = 0
    for ref in references:
        if ref and ref.startswith("CN-"):
            try:
                num = int(ref.replace("CN-", "").strip())
                if num > max_num:
                    max_num = num
            except ValueError:
                continue
    return f"CN-{max_num + 1:06d}"


async def generate_refund_number(session: AsyncSession, organization_id: uuid.UUID) -> str:
    stmt = (
        select(PaymentRefund.refund_number)
        .where(PaymentRefund.organization_id == organization_id)
        .order_by(PaymentRefund.created_at.desc(), PaymentRefund.refund_number.desc())
        .limit(20)
    )
    references = (await session.execute(stmt)).scalars().all()
    max_num = 0
    for ref in references:
        if ref and ref.startswith("RFD-"):
            try:
                num = int(ref.replace("RFD-", "").strip())
                if num > max_num:
                    max_num = num
            except ValueError:
                continue
    return f"RFD-{max_num + 1:06d}"


async def create_credit_note(
    session: AsyncSession,
    organization_id: uuid.UUID,
    payload: CreditNoteCreateRequest,
    current_user: Optional[User] = None,
) -> CreditNote:
    # 1. Fetch & validate invoice with row-level lock
    inv_stmt = (
        select(Invoice)
        .where(Invoice.id == payload.invoice_id, Invoice.organization_id == organization_id)
        .with_for_update()
    )
    invoice = (await session.execute(inv_stmt)).scalar_one_or_none()
    if not invoice:
        raise NotFoundException(f"Invoice {payload.invoice_id} not found")

    if invoice.status in ["DRAFT", "VOID"]:
        raise BusinessRuleViolationException(f"Credit note cannot be issued against an invoice in status '{invoice.status}'.")

    # Calculate existing total credits issued for this invoice
    cn_stmt = select(func.coalesce(func.sum(CreditNote.total), 0)).where(
        CreditNote.organization_id == organization_id,
        CreditNote.invoice_id == payload.invoice_id,
        CreditNote.status != "VOID",
    )
    previously_credited = Decimal(str((await session.execute(cn_stmt)).scalar() or 0))
    max_allowed_credit = invoice.total - previously_credited

    cn_number = await generate_credit_note_number(session, organization_id)

    credit_note = CreditNote(
        organization_id=organization_id,
        credit_note_number=cn_number,
        invoice_id=invoice.id,
        customer_id=invoice.customer_id,
        reason=payload.reason,
        status="ISSUED",
        created_by_user_id=current_user.id if current_user else None,
    )
    session.add(credit_note)
    await session.flush()

    subtotal = Decimal("0.00")
    for item_data in payload.items:
        qty = Decimal(str(item_data.quantity))
        u_price = Decimal(str(item_data.unit_price))
        amt = qty * u_price
        subtotal += amt

        cn_item = CreditNoteItem(
            organization_id=organization_id,
            credit_note_id=credit_note.id,
            description=item_data.description,
            quantity=qty,
            unit_price=u_price,
            amount=amt,
        )
        session.add(cn_item)

    credit_note.subtotal = subtotal
    credit_note.tax_total = Decimal("0.00")
    credit_note.total = subtotal

    if credit_note.total <= Decimal("0.00"):
        raise BusinessRuleViolationException("Credit note total must be greater than zero.")

    if credit_note.total > max_allowed_credit:
        raise BusinessRuleViolationException(f"Credit note total ({credit_note.total}) exceeds maximum allowable credit ({max_allowed_credit}) for this invoice.")

    # Deduct credit note total from invoice amount_due (down to 0 min)
    invoice.amount_due = max(Decimal("0.00"), invoice.amount_due - credit_note.total)
    if invoice.amount_due == Decimal("0.00") and invoice.amount_paid > Decimal("0.00"):
        invoice.status = "PAID"

    await session.commit()
    await session.refresh(credit_note)
    return credit_note


async def record_payment_refund(
    session: AsyncSession,
    organization_id: uuid.UUID,
    payload: PaymentRefundCreateRequest,
    current_user: Optional[User] = None,
) -> PaymentRefund:
    # 1. Fetch & validate payment with row-level lock
    pay_stmt = (
        select(Payment)
        .where(Payment.id == payload.payment_id, Payment.organization_id == organization_id)
        .with_for_update()
    )
    payment = (await session.execute(pay_stmt)).scalar_one_or_none()
    if not payment:
        raise NotFoundException(f"Payment {payload.payment_id} not found")

    if payment.status != "COMPLETED":
        raise BusinessRuleViolationException(f"Refunds can only be recorded against COMPLETED payments.")

    # Calculate existing refunds for this payment
    rfd_stmt = select(func.coalesce(func.sum(PaymentRefund.amount), 0)).where(
        PaymentRefund.organization_id == organization_id,
        PaymentRefund.payment_id == payload.payment_id,
        PaymentRefund.status != "VOID",
    )
    previously_refunded = Decimal(str((await session.execute(rfd_stmt)).scalar() or 0))
    max_allowed_refund = payment.amount - previously_refunded

    refund_amt = Decimal(str(payload.amount))
    if refund_amt <= Decimal("0.00"):
        raise BusinessRuleViolationException("Refund amount must be greater than zero.")

    if refund_amt > max_allowed_refund:
        raise BusinessRuleViolationException(f"Refund amount ({refund_amt}) exceeds maximum allowable refund ({max_allowed_refund}) for this payment.")

    refund_num = await generate_refund_number(session, organization_id)
    rfd_date = payload.refund_date or date.today()

    refund = PaymentRefund(
        organization_id=organization_id,
        refund_number=refund_num,
        payment_id=payment.id,
        credit_note_id=payload.credit_note_id,
        amount=refund_amt,
        reason=payload.reason,
        refund_date=rfd_date,
        status="COMPLETED",
        created_by_user_id=current_user.id if current_user else None,
    )
    session.add(refund)

    await session.commit()
    await session.refresh(refund)
    return refund


async def get_credit_note(session: AsyncSession, organization_id: uuid.UUID, credit_note_id: uuid.UUID) -> CreditNote:
    stmt = select(CreditNote).where(CreditNote.id == credit_note_id, CreditNote.organization_id == organization_id)
    cn = (await session.execute(stmt)).scalar_one_or_none()
    if not cn:
        raise NotFoundException(f"CreditNote {credit_note_id} not found")
    return cn


async def list_credit_notes_for_invoice(session: AsyncSession, organization_id: uuid.UUID, invoice_id: uuid.UUID) -> List[CreditNote]:
    stmt = select(CreditNote).where(CreditNote.organization_id == organization_id, CreditNote.invoice_id == invoice_id).order_by(CreditNote.created_at.desc())
    return list((await session.execute(stmt)).scalars().all())


async def list_refunds_for_payment(session: AsyncSession, organization_id: uuid.UUID, payment_id: uuid.UUID) -> List[PaymentRefund]:
    stmt = select(PaymentRefund).where(PaymentRefund.organization_id == organization_id, PaymentRefund.payment_id == payment_id).order_by(PaymentRefund.created_at.desc())
    return list((await session.execute(stmt)).scalars().all())
