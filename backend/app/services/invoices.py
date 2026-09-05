import uuid
from decimal import Decimal
from datetime import date, timedelta
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete
from app.models.invoice import Invoice, InvoiceItem
from app.models.quotation import Quotation, QuotationItem
from app.models.customer import Customer
from app.schemas.invoices import InvoiceCreateRequest, InvoiceUpdateRequest
from app.core.exceptions import NotFoundException, BusinessRuleViolationException


from sqlalchemy.orm import selectinload


async def calculate_invoice_totals(invoice: Invoice, items: Optional[List[InvoiceItem]] = None) -> None:
    """Recalculates invoice subtotal, discount_total, tax_total, total, and amount_due deterministically."""
    subtotal = Decimal("0.00")
    discount_total = Decimal("0.00")
    tax_total = Decimal("0.00")

    target_items = items if items is not None else invoice.items

    for item in target_items:
        item.line_subtotal = Decimal(str(item.quantity)) * Decimal(str(item.unit_price))
        item.line_total = item.line_subtotal - Decimal(str(item.discount_amount)) + Decimal(str(item.tax_amount))
        subtotal += item.line_subtotal
        discount_total += Decimal(str(item.discount_amount))
        tax_total += Decimal(str(item.tax_amount))

    invoice.subtotal = subtotal
    invoice.discount_total = discount_total
    invoice.tax_total = tax_total
    invoice.total = subtotal - discount_total + tax_total
    invoice.amount_due = invoice.total - invoice.amount_paid


async def generate_invoice_number(session: AsyncSession, organization_id: uuid.UUID) -> str:
    stmt = select(func.count(Invoice.id)).where(Invoice.organization_id == organization_id)
    count = int((await session.execute(stmt)).scalar() or 0) + 1
    return f"INV-{count:06d}"


async def create_invoice(
    session: AsyncSession,
    organization_id: uuid.UUID,
    payload: InvoiceCreateRequest,
) -> Invoice:
    # 1. Validate customer
    c_stmt = select(Customer).where(Customer.id == payload.customer_id, Customer.organization_id == organization_id)
    customer = (await session.execute(c_stmt)).scalar_one_or_none()
    if not customer:
        raise NotFoundException(f"Customer {payload.customer_id} not found")

    invoice_number = await generate_invoice_number(session, organization_id)
    inv_date = payload.invoice_date or date.today()
    due_dt = payload.due_date or (inv_date + timedelta(days=30))

    invoice = Invoice(
        organization_id=organization_id,
        invoice_number=invoice_number,
        customer_id=payload.customer_id,
        quotation_id=payload.quotation_id,
        currency=payload.currency or "USD",
        invoice_date=inv_date,
        due_date=due_dt,
        status="DRAFT",
    )
    session.add(invoice)
    await session.flush()

    items_list: List[InvoiceItem] = []
    for item_data in payload.items:
        item = InvoiceItem(
            organization_id=organization_id,
            invoice_id=invoice.id,
            product_id=item_data.product_id,
            product_variant_id=item_data.product_variant_id,
            quotation_item_id=item_data.quotation_item_id,
            description=item_data.description,
            quantity=item_data.quantity,
            unit_price=item_data.unit_price,
            discount_amount=item_data.discount_amount,
            tax_amount=item_data.tax_amount,
            billing_type=item_data.billing_type or "ONE_TIME",
        )
        session.add(item)
        items_list.append(item)

    await calculate_invoice_totals(invoice, items_list)
    await session.commit()

    return await get_invoice(session, organization_id, invoice.id)


async def create_invoice_from_quotation(
    session: AsyncSession,
    organization_id: uuid.UUID,
    quotation_id: uuid.UUID,
) -> Invoice:
    # Check quotation state
    q_stmt = select(Quotation).where(Quotation.id == quotation_id, Quotation.organization_id == organization_id)
    quotation = (await session.execute(q_stmt)).scalar_one_or_none()
    if not quotation:
        raise NotFoundException(f"Quotation {quotation_id} not found")

    if quotation.status in ["draft", "rejected", "cancelled", "expired"]:
        raise BusinessRuleViolationException(f"Cannot invoice quotation in status '{quotation.status}'. Must be accepted or converted.")

    # Check for existing invoice
    exist_stmt = select(Invoice).where(Invoice.organization_id == organization_id, Invoice.quotation_id == quotation_id, Invoice.status != "VOID")
    existing_inv = (await session.execute(exist_stmt)).scalar_one_or_none()
    if existing_inv:
        return await get_invoice(session, organization_id, existing_inv.id)

    items_stmt = select(QuotationItem).where(QuotationItem.quotation_id == quotation_id)
    items = list((await session.execute(items_stmt)).scalars().all())

    invoice_number = await generate_invoice_number(session, organization_id)
    inv_date = date.today()
    due_dt = inv_date + timedelta(days=30)

    invoice = Invoice(
        organization_id=organization_id,
        invoice_number=invoice_number,
        customer_id=quotation.customer_id,
        quotation_id=quotation.id,
        currency=quotation.currency or "USD",
        invoice_date=inv_date,
        due_date=due_dt,
        status="DRAFT",
    )
    session.add(invoice)
    await session.flush()

    items_list: List[InvoiceItem] = []
    for item in items:
        inv_item = InvoiceItem(
            organization_id=organization_id,
            invoice_id=invoice.id,
            product_id=item.product_id,
            product_variant_id=item.product_variant_id,
            quotation_item_id=item.id,
            description=item.product_name,
            quantity=item.quantity,
            unit_price=item.unit_price,
            discount_amount=item.discount_amount or Decimal("0.00"),
            tax_amount=item.tax_amount or Decimal("0.00"),
            billing_type="ONE_TIME",
        )
        session.add(inv_item)
        items_list.append(inv_item)

    await calculate_invoice_totals(invoice, items_list)
    await session.commit()
    return await get_invoice(session, organization_id, invoice.id)


async def issue_invoice(session: AsyncSession, organization_id: uuid.UUID, invoice_id: uuid.UUID) -> Invoice:
    inv_stmt = select(Invoice).where(Invoice.id == invoice_id, Invoice.organization_id == organization_id)
    invoice = (await session.execute(inv_stmt)).scalar_one_or_none()
    if not invoice:
        raise NotFoundException(f"Invoice {invoice_id} not found")

    if invoice.status != "DRAFT":
        raise BusinessRuleViolationException(f"Invoice in status '{invoice.status}' cannot be issued. Must be DRAFT.")

    invoice.status = "ISSUED"
    await session.commit()
    return await get_invoice(session, organization_id, invoice_id)


async def void_invoice(session: AsyncSession, organization_id: uuid.UUID, invoice_id: uuid.UUID) -> Invoice:
    inv_stmt = select(Invoice).where(Invoice.id == invoice_id, Invoice.organization_id == organization_id)
    invoice = (await session.execute(inv_stmt)).scalar_one_or_none()
    if not invoice:
        raise NotFoundException(f"Invoice {invoice_id} not found")

    if invoice.amount_paid > Decimal("0.00"):
        raise BusinessRuleViolationException("Cannot void an invoice with recorded payments. Issue a refund/credit note instead.")

    invoice.status = "VOID"
    await session.commit()
    return await get_invoice(session, organization_id, invoice_id)


async def get_invoice(session: AsyncSession, organization_id: uuid.UUID, invoice_id: uuid.UUID) -> Invoice:
    stmt = select(Invoice).options(selectinload(Invoice.items)).where(Invoice.id == invoice_id, Invoice.organization_id == organization_id)
    invoice = (await session.execute(stmt)).scalar_one_or_none()
    if not invoice:
        raise NotFoundException(f"Invoice {invoice_id} not found")
    return invoice


async def list_invoices(session: AsyncSession, organization_id: uuid.UUID, customer_id: Optional[uuid.UUID] = None) -> List[Invoice]:
    stmt = select(Invoice).options(selectinload(Invoice.items)).where(Invoice.organization_id == organization_id)
    if customer_id:
        stmt = stmt.where(Invoice.customer_id == customer_id)
    stmt = stmt.order_by(Invoice.created_at.desc())
    return list((await session.execute(stmt)).scalars().all())

