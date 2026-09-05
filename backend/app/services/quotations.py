import uuid
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime, timezone
from typing import List, Optional, Tuple
from sqlalchemy import select, func, or_
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
import logging

from app.models.quotation import Quotation, QuotationItem
from app.models.customer import Customer
from app.models.contact import Contact
from app.models.deal import Deal
from app.models.product import Product
from app.schemas.quotation import QuotationCreate, QuotationUpdate, QuotationItemCreate
from app.core.exceptions import NotFoundException, ConflictException, BusinessRuleViolationException

logger = logging.getLogger("dealflow360.quotations_service")

TWO_DECIMALS = Decimal("0.01")


def round_decimal(val: Decimal) -> Decimal:
    """Rounds monetary decimal values consistently to two decimal places."""
    return val.quantize(TWO_DECIMALS, rounding=ROUND_HALF_UP)


async def generate_quotation_number(db: AsyncSession, organization_id: uuid.UUID) -> str:
    """Generates the next sequential quotation number for the organization (e.g. QT-000001)."""
    stmt = (
        select(Quotation.quotation_number)
        .where(
            Quotation.organization_id == organization_id,
            Quotation.quotation_number.like("QT-%")
        )
        .order_by(Quotation.created_at.desc(), Quotation.quotation_number.desc())
        .limit(20)
    )
    result = await db.execute(stmt)
    numbers = result.scalars().all()

    max_num = 0
    for num_str in numbers:
        try:
            num_part = int(num_str.replace("QT-", ""))
            if num_part > max_num:
                max_num = num_part
        except ValueError:
            continue

    if max_num == 0:
        count_stmt = select(func.count(Quotation.id)).where(Quotation.organization_id == organization_id)
        max_num = int((await db.execute(count_stmt)).scalar() or 0)

    next_num = max_num + 1
    return f"QT-{next_num:06d}"


def validate_status_transition(current_status: str, new_status: str) -> None:
    """Validates allowed state machine status transitions for Quotations."""
    from app.services.quotation_state import can_transition
    if not can_transition(current_status, new_status):
        raise BusinessRuleViolationException(
            f"Invalid quotation status transition from '{current_status}' to '{new_status}'."
        )


async def verify_customer_in_tenant(db: AsyncSession, organization_id: uuid.UUID, customer_id: uuid.UUID) -> Customer:
    """Verifies target customer exists within the user's organization and is active."""
    stmt = select(Customer).where(
        Customer.id == customer_id,
        Customer.organization_id == organization_id
    )
    result = await db.execute(stmt)
    customer = result.scalar_one_or_none()
    if not customer:
        raise NotFoundException("Target customer requested was not found")
    if hasattr(customer, 'is_active') and not customer.is_active:
        raise BusinessRuleViolationException("Target customer is inactive and cannot receive new quotations")
    return customer


async def verify_contact_in_tenant(
    db: AsyncSession,
    organization_id: uuid.UUID,
    customer_id: uuid.UUID,
    contact_id: uuid.UUID
) -> Contact:
    """Verifies target contact exists within user's organization and belongs to target customer."""
    stmt = select(Contact).where(
        Contact.id == contact_id,
        Contact.organization_id == organization_id,
        Contact.customer_id == customer_id
    )
    result = await db.execute(stmt)
    contact = result.scalar_one_or_none()
    if not contact:
        raise NotFoundException("Target contact requested was not found or does not belong to target customer")
    return contact


async def verify_deal_in_tenant(
    db: AsyncSession,
    organization_id: uuid.UUID,
    customer_id: uuid.UUID,
    deal_id: uuid.UUID
) -> Deal:
    """Verifies target deal exists within user's organization and belongs to target customer."""
    stmt = select(Deal).where(
        Deal.id == deal_id,
        Deal.organization_id == organization_id,
        Deal.customer_id == customer_id
    )
    result = await db.execute(stmt)
    deal = result.scalar_one_or_none()
    if not deal:
        raise NotFoundException("Target deal requested was not found or does not belong to target customer")
    return deal


async def verify_product_in_tenant(db: AsyncSession, organization_id: uuid.UUID, product_id: uuid.UUID) -> Product:
    """Verifies target product exists within the user's organization and is active."""
    stmt = select(Product).where(
        Product.id == product_id,
        Product.organization_id == organization_id
    )
    result = await db.execute(stmt)
    product = result.scalar_one_or_none()
    if not product:
        raise NotFoundException("Target product requested was not found")
    if hasattr(product, 'is_active') and not product.is_active:
        raise BusinessRuleViolationException(f"Product '{product.name}' is inactive and cannot be added to a quotation")
    return product


async def calculate_line_items_and_totals(
    db: AsyncSession,
    organization_id: uuid.UUID,
    item_inputs: List[QuotationItemCreate],
    discount_amount: Decimal,
    tax_amount: Decimal,
    customer_id: Optional[uuid.UUID] = None,
    quotation_date: Optional[datetime] = None
) -> Tuple[List[QuotationItem], Decimal, Decimal]:
    """
    Validates products, resolves pricing via Pricing Engine rules (or manual override), captures historical price & SKU snapshots, and calculates line totals, subtotal, and total amount.
    """
    if not item_inputs:
        raise BusinessRuleViolationException("Quotation must contain at least one item")

    items: List[QuotationItem] = []
    subtotal = Decimal("0.00")

    for idx, item_input in enumerate(item_inputs):
        if item_input.quantity <= Decimal("0.00"):
            raise BusinessRuleViolationException("Item quantity must be greater than zero")

        if item_input.unit_price is not None and item_input.unit_price < Decimal("0.00"):
            raise BusinessRuleViolationException("Line item unit price cannot be negative")

        product = await verify_product_in_tenant(db, organization_id, item_input.product_id)

        # Sequence assignment: use client sequence if provided, otherwise auto-sequence 1-indexed
        seq = item_input.sequence if item_input.sequence > 0 else (idx + 1)

        # HISTORICAL PRICE & SKU SNAPSHOT via PRICING ENGINE / MANUAL OVERRIDE
        if item_input.unit_price is not None:
            unit_price = round_decimal(item_input.unit_price)
        else:
            from app.services import pricing as pricing_service
            from app.schemas.pricing import PricingCalculateRequest
            pricing_res = await pricing_service.calculate_item_price(
                db,
                organization_id,
                PricingCalculateRequest(
                    product_id=product.id,
                    quantity=item_input.quantity,
                    customer_id=customer_id,
                    quotation_date=quotation_date
                )
            )
            unit_price = pricing_res.final_unit_price

        # HISTORICAL COST SNAPSHOT
        unit_cost = round_decimal(item_input.unit_cost) if item_input.unit_cost is not None else round_decimal(getattr(product, "unit_cost", Decimal("0.00")) or Decimal("0.00"))

        quantity = round_decimal(item_input.quantity)
        disc_amt = round_decimal(item_input.discount_amount)
        tax_amt = round_decimal(item_input.tax_amount)

        base_line_total = round_decimal(quantity * unit_price)
        line_total = round_decimal(base_line_total - disc_amt + tax_amt)

        q_item = QuotationItem(
            product_id=product.id,
            product_variant_id=item_input.product_variant_id,
            product_name=product.name,
            sku=product.sku,
            description=item_input.description.strip() if item_input.description else None,
            sequence=seq,
            quantity=quantity,
            unit_price=unit_price,
            unit_cost=unit_cost,
            discount_percent=round_decimal(item_input.discount_percent),
            discount_amount=disc_amt,
            tax_rate=round_decimal(item_input.tax_rate),
            tax_amount=tax_amt,
            line_total=line_total
        )
        items.append(q_item)
        subtotal += line_total

    subtotal = round_decimal(subtotal)
    discount = round_decimal(discount_amount)
    tax = round_decimal(tax_amount)

    if discount > subtotal:
        raise BusinessRuleViolationException("Discount amount cannot exceed quotation subtotal")

    total_amount = round_decimal(subtotal - discount + tax)
    if total_amount < Decimal("0.00"):
        raise BusinessRuleViolationException("Total quotation amount cannot be negative")

    return items, subtotal, total_amount


async def create_quotation(
    db: AsyncSession,
    organization_id: uuid.UUID,
    payload: QuotationCreate,
    current_user_id: Optional[uuid.UUID] = None
) -> Quotation:
    """Atomically creates a new Quotation with price-snapshot line items."""
    # 1. Customer tenant security check & active validation
    await verify_customer_in_tenant(db, organization_id, payload.customer_id)

    # 2. Optional Contact & Deal relationship security checks
    if payload.contact_id:
        await verify_contact_in_tenant(db, organization_id, payload.customer_id, payload.contact_id)

    if payload.deal_id:
        await verify_deal_in_tenant(db, organization_id, payload.customer_id, payload.deal_id)

    # 3. Date validation: valid_until cannot be earlier than quotation_date
    quot_date = payload.quotation_date or datetime.now(timezone.utc)
    if quot_date.tzinfo is None:
        quot_date = quot_date.replace(tzinfo=timezone.utc)

    if payload.valid_until:
        v_dt = payload.valid_until
        if v_dt.tzinfo is None:
            v_dt = v_dt.replace(tzinfo=timezone.utc)
        if v_dt < quot_date:
            raise BusinessRuleViolationException("Expiration date (valid_until) cannot be earlier than quotation issuance date")

    # 4. Line calculations and historical price snapshots
    items, subtotal, total_amount = await calculate_line_items_and_totals(
        db,
        organization_id,
        payload.items,
        payload.discount_amount,
        payload.tax_amount,
        customer_id=payload.customer_id,
        quotation_date=quot_date
    )

    # 5. Generate tenant-scoped quotation number
    quotation_number = await generate_quotation_number(db, organization_id)

    quotation = Quotation(
        organization_id=organization_id,
        customer_id=payload.customer_id,
        contact_id=payload.contact_id,
        deal_id=payload.deal_id,
        title=payload.title.strip() if payload.title else None,
        quotation_number=quotation_number,
        status="draft",
        currency=payload.currency.upper(),
        quotation_date=quot_date,
        valid_until=payload.valid_until,
        notes=payload.notes.strip() if payload.notes else None,
        terms=payload.terms.strip() if payload.terms else None,
        created_by_user_id=current_user_id,
        subtotal=subtotal,
        discount_amount=round_decimal(payload.discount_amount),
        tax_amount=round_decimal(payload.tax_amount),
        total_amount=total_amount,
        items=items
    )

    try:
        db.add(quotation)
        await db.flush()

        from app.services.quotation_state import log_state_history
        await log_state_history(
            db,
            organization_id=organization_id,
            quotation_id=quotation.id,
            from_status=None,
            to_status="draft",
            changed_by_user_id=current_user_id,
            reason="Initial draft created"
        )
    except IntegrityError as exc:
        await db.rollback()
        error_msg = str(exc)
        logger.warning(f"Quotation creation failed: {error_msg}")
        if "uq_quotations_organization_id_quotation_number" in error_msg:
            raise ConflictException("Quotation number collision occurred; please retry.")
        raise BusinessRuleViolationException("Quotation creation failed due to a database constraint violation.")

    # Re-fetch with eager loaded relationships
    return await get_quotation_by_id(db, organization_id, quotation.id)


async def list_quotations(
    db: AsyncSession,
    organization_id: uuid.UUID,
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    customer_id: Optional[uuid.UUID] = None,
    search: Optional[str] = None
) -> List[Quotation]:
    """Retrieves quotations scoped strictly to the specified organization."""
    stmt = (
        select(Quotation)
        .options(selectinload(Quotation.items))
        .where(Quotation.organization_id == organization_id)
    )

    if status:
        stmt = stmt.where(Quotation.status == status.strip().lower())
    if customer_id:
        stmt = stmt.where(Quotation.customer_id == customer_id)
    if search:
        pattern = f"%{search.strip()}%"
        stmt = stmt.where(Quotation.quotation_number.ilike(pattern))

    stmt = stmt.order_by(Quotation.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_quotation_by_id(
    db: AsyncSession,
    organization_id: uuid.UUID,
    quotation_id: uuid.UUID
) -> Quotation:
    """Fetches a quotation by ID within tenant scope (raises 404 if missing or cross-tenant)."""
    stmt = (
        select(Quotation)
        .options(selectinload(Quotation.items))
        .where(
            Quotation.id == quotation_id,
            Quotation.organization_id == organization_id
        )
    )
    result = await db.execute(stmt)
    quotation = result.scalar_one_or_none()
    if not quotation:
        raise NotFoundException("Quotation requested was not found")

    from app.services.quotation_state import check_lazy_expiration
    await check_lazy_expiration(db, organization_id, quotation)

    return quotation


async def update_quotation(
    db: AsyncSession,
    organization_id: uuid.UUID,
    quotation_id: uuid.UUID,
    payload: QuotationUpdate,
    current_user_id: Optional[uuid.UUID] = None
) -> Quotation:
    """Updates an existing quotation within tenant scope."""
    from app.services.quotation_state import is_status_immutable, log_state_history

    quotation = await get_quotation_by_id(db, organization_id, quotation_id)
    update_data = payload.model_dump(exclude_unset=True)

    # 1. Immutability checks for locked states
    if is_status_immutable(quotation.status):
        commercial_fields = {"items", "customer_id", "discount_amount", "tax_amount", "currency"}
        attempted_commercial = set(update_data.keys()).intersection(commercial_fields)
        if attempted_commercial:
            raise BusinessRuleViolationException(
                f"Quotation with status '{quotation.status}' is locked. Cannot modify commercial fields ({', '.join(sorted(attempted_commercial))})."
            )

        if quotation.status in {"accepted", "rejected", "expired", "cancelled", "converted"}:
            non_status_changes = set(update_data.keys()) - {"status"}
            if non_status_changes:
                raise BusinessRuleViolationException(
                    f"Finalized quotation with status '{quotation.status}' cannot be modified."
                )

    # 2. Validate status transition and log history if status is being updated
    old_status = quotation.status
    if "status" in update_data and update_data["status"] is not None:
        new_status = update_data["status"].strip().lower()
        if old_status != new_status:
            validate_status_transition(old_status, new_status)
            quotation.status = new_status
            await log_state_history(
                db,
                organization_id=organization_id,
                quotation_id=quotation.id,
                from_status=old_status,
                to_status=new_status,
                changed_by_user_id=current_user_id,
                reason="Updated via API update request"
            )

    # 3. Customer, Contact, Deal reassignment validation
    target_customer_id = update_data.get("customer_id", quotation.customer_id)
    if "customer_id" in update_data and update_data["customer_id"] is not None:
        await verify_customer_in_tenant(db, organization_id, update_data["customer_id"])
        quotation.customer_id = update_data["customer_id"]

    if "contact_id" in update_data:
        if update_data["contact_id"] is not None:
            await verify_contact_in_tenant(db, organization_id, target_customer_id, update_data["contact_id"])
        quotation.contact_id = update_data["contact_id"]

    if "deal_id" in update_data:
        if update_data["deal_id"] is not None:
            await verify_deal_in_tenant(db, organization_id, target_customer_id, update_data["deal_id"])
        quotation.deal_id = update_data["deal_id"]

    # 4. Fields: Title, Currency, Dates, Notes, Terms
    if "title" in update_data:
        quotation.title = update_data["title"].strip() if update_data["title"] else None
    if "currency" in update_data and update_data["currency"] is not None:
        quotation.currency = update_data["currency"].upper()
    if "quotation_date" in update_data and update_data["quotation_date"] is not None:
        quotation.quotation_date = update_data["quotation_date"]
    if "valid_until" in update_data:
        quotation.valid_until = update_data["valid_until"]
    if "notes" in update_data:
        quotation.notes = update_data["notes"].strip() if update_data["notes"] else None
    if "terms" in update_data:
        quotation.terms = update_data["terms"].strip() if update_data["terms"] else None

    if current_user_id:
        quotation.updated_by_user_id = current_user_id

    # 5. Items or Financial Adjustments
    items_updated = "items" in update_data and update_data["items"] is not None
    discount_updated = "discount_amount" in update_data and update_data["discount_amount"] is not None
    tax_updated = "tax_amount" in update_data and update_data["tax_amount"] is not None

    if items_updated:
        # Recalculate line items from provided list
        item_inputs = payload.items
        discount = payload.discount_amount if discount_updated else quotation.discount_amount
        tax = payload.tax_amount if tax_updated else quotation.tax_amount

        new_items, subtotal, total_amount = await calculate_line_items_and_totals(
            db, organization_id, item_inputs, discount, tax,
            customer_id=target_customer_id,
            quotation_date=quotation.quotation_date
        )

        quotation.items.clear()
        quotation.items.extend(new_items)
        quotation.subtotal = subtotal
        quotation.discount_amount = round_decimal(discount)
        quotation.tax_amount = round_decimal(tax)
        quotation.total_amount = total_amount
    elif discount_updated or tax_updated:
        discount = payload.discount_amount if discount_updated else quotation.discount_amount
        tax = payload.tax_amount if tax_updated else quotation.tax_amount
        discount = round_decimal(discount)
        tax = round_decimal(tax)

        if discount > quotation.subtotal:
            raise BusinessRuleViolationException("Discount amount cannot exceed quotation subtotal")

        total_amount = round_decimal(quotation.subtotal - discount + tax)
        if total_amount < Decimal("0.00"):
            raise BusinessRuleViolationException("Total quotation amount cannot be negative")

        quotation.discount_amount = discount
        quotation.tax_amount = tax
        quotation.total_amount = total_amount

    # 6. Commercial edit invalidates existing approval
    if items_updated or discount_updated or tax_updated or ("customer_id" in update_data):
        from app.services.approval_engine import invalidate_quotation_approval
        await invalidate_quotation_approval(db, organization_id, quotation.id)

    try:
        await db.flush()
    except IntegrityError as exc:
        await db.rollback()
        raise BusinessRuleViolationException("Quotation update failed due to a database constraint violation.")

    return await get_quotation_by_id(db, organization_id, quotation.id)


async def delete_quotation(
    db: AsyncSession,
    organization_id: uuid.UUID,
    quotation_id: uuid.UUID
) -> None:
    """Deletes a quotation and its line items within tenant scope."""
    quotation = await get_quotation_by_id(db, organization_id, quotation_id)
    await db.delete(quotation)
    await db.flush()

