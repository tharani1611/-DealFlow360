import uuid
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.models.quotation import Quotation, QuotationItem
from app.models.quotation_line_comment import QuotationLineComment
from app.models.quotation_change_request import QuotationChangeRequest
from app.models.quotation_version import QuotationVersion
from app.models.portal_user import PortalUser
from app.models.user import User
from app.schemas.negotiation import LineCommentCreate, ChangeRequestCreate, ChangeRequestReview, CounterDiscountApply
from app.services import quotations as quotation_service
from app.services import approval_engine
from app.core.exceptions import NotFoundException, BusinessRuleViolationException, ForbiddenException

logger = logging.getLogger("dealflow360.negotiation_service")

TWO_DECIMALS = Decimal("0.01")


def round_decimal(val: Decimal) -> Decimal:
    return val.quantize(TWO_DECIMALS, rounding=ROUND_HALF_UP)


# --- 1. Line Comments ---

async def create_line_comment(
    db: AsyncSession,
    organization_id: uuid.UUID,
    quotation_id: uuid.UUID,
    payload: LineCommentCreate,
    author_user: Optional[User] = None,
    author_portal_user: Optional[PortalUser] = None
) -> QuotationLineComment:
    """Creates line-level comment for a quotation item."""
    # Verify quotation exists in tenant
    quotation = await quotation_service.get_quotation_by_id(db, organization_id, quotation_id)

    # Verify item exists on quotation
    item = next((i for i in quotation.items if i.id == payload.quotation_item_id), None)
    if not item:
        raise NotFoundException("Target quotation item was not found on this quotation")

    if author_user:
        author_type = "INTERNAL_USER"
        author_user_id = author_user.id
        author_portal_user_id = None
        author_name = author_user.full_name or author_user.email
        is_internal = payload.is_internal_only
    elif author_portal_user:
        author_type = "CUSTOMER_PORTAL"
        author_user_id = None
        author_portal_user_id = author_portal_user.id
        author_name = author_portal_user.full_name
        is_internal = False  # Portal user comments are never internal-only
    else:
        raise BusinessRuleViolationException("Author must be specified")

    comment = QuotationLineComment(
        organization_id=organization_id,
        quotation_id=quotation_id,
        quotation_item_id=payload.quotation_item_id,
        author_type=author_type,
        author_user_id=author_user_id,
        author_portal_user_id=author_portal_user_id,
        author_name=author_name,
        comment_text=payload.comment_text.strip(),
        is_internal_only=is_internal,
        created_at=datetime.now(timezone.utc)
    )

    db.add(comment)
    await db.flush()
    return comment


async def list_line_comments(
    db: AsyncSession,
    organization_id: uuid.UUID,
    quotation_id: uuid.UUID,
    quotation_item_id: Optional[uuid.UUID] = None,
    is_portal: bool = False
) -> List[QuotationLineComment]:
    """Lists line comments. Hides internal-only comments from portal users."""
    stmt = (
        select(QuotationLineComment)
        .where(
            QuotationLineComment.organization_id == organization_id,
            QuotationLineComment.quotation_id == quotation_id
        )
    )

    if quotation_item_id:
        stmt = stmt.where(QuotationLineComment.quotation_item_id == quotation_item_id)

    if is_portal:
        stmt = stmt.where(QuotationLineComment.is_internal_only == False)

    stmt = stmt.order_by(QuotationLineComment.created_at.asc())
    result = await db.execute(stmt)
    return list(result.scalars().all())


# --- 2. Change Requests & Counter-Discounts ---

async def create_change_request(
    db: AsyncSession,
    portal_user: PortalUser,
    quotation_id: uuid.UUID,
    payload: ChangeRequestCreate
) -> QuotationChangeRequest:
    """Creates a customer change request / counter discount proposal from portal."""
    # Verify quotation exists for customer
    stmt = select(Quotation).where(
        Quotation.id == quotation_id,
        Quotation.organization_id == portal_user.organization_id,
        Quotation.customer_id == portal_user.customer_id
    )
    res = await db.execute(stmt)
    quotation = res.scalar_one_or_none()
    if not quotation or quotation.status not in ("sent", "accepted"):
        raise BusinessRuleViolationException("Change request can only be submitted for sent or active quotations.")

    cr = QuotationChangeRequest(
        organization_id=portal_user.organization_id,
        quotation_id=quotation_id,
        quotation_item_id=payload.quotation_item_id,
        requested_by_portal_user_id=portal_user.id,
        change_type=payload.change_type.strip(),
        status="OPEN",
        requested_discount_percent=round_decimal(payload.requested_discount_percent) if payload.requested_discount_percent is not None else None,
        requested_quantity=round_decimal(payload.requested_quantity) if payload.requested_quantity is not None else None,
        request_details=payload.request_details.strip()
    )

    db.add(cr)
    await db.flush()
    return cr


async def list_change_requests(
    db: AsyncSession,
    organization_id: uuid.UUID,
    quotation_id: uuid.UUID
) -> List[QuotationChangeRequest]:
    """Lists change requests for a quotation."""
    stmt = (
        select(QuotationChangeRequest)
        .where(
            QuotationChangeRequest.organization_id == organization_id,
            QuotationChangeRequest.quotation_id == quotation_id
        )
        .order_by(QuotationChangeRequest.created_at.desc())
    )
    res = await db.execute(stmt)
    return list(res.scalars().all())


async def review_change_request(
    db: AsyncSession,
    organization_id: uuid.UUID,
    quotation_id: uuid.UUID,
    change_request_id: uuid.UUID,
    reviewer_user: User,
    payload: ChangeRequestReview
) -> QuotationChangeRequest:
    """Reviews (accepts or rejects) a customer change request."""
    stmt = select(QuotationChangeRequest).where(
        QuotationChangeRequest.id == change_request_id,
        QuotationChangeRequest.organization_id == organization_id,
        QuotationChangeRequest.quotation_id == quotation_id
    )
    res = await db.execute(stmt)
    cr = res.scalar_one_or_none()
    if not cr:
        raise NotFoundException("Change request not found")

    status_clean = payload.status.strip().upper()
    if status_clean not in ("ACCEPTED", "REJECTED"):
        raise BusinessRuleViolationException("Status must be ACCEPTED or REJECTED")

    cr.status = status_clean
    cr.response_note = payload.response_note.strip() if payload.response_note else None
    cr.reviewed_by_user_id = reviewer_user.id
    cr.reviewed_at = datetime.now(timezone.utc)

    await db.flush()
    return cr


async def apply_counter_discount(
    db: AsyncSession,
    organization_id: uuid.UUID,
    quotation_id: uuid.UUID,
    user: User,
    payload: CounterDiscountApply
) -> Quotation:
    """
    Applies counter-discount adjustments to a quotation line item or overall,
    recalculates pricing/margins/totals with Decimal precision, invalidates existing approval,
    and creates a new version snapshot.
    """
    quotation = await quotation_service.get_quotation_by_id(db, organization_id, quotation_id)

    # First take snapshot of current version BEFORE applying changes
    await create_quotation_version_snapshot(
        db, organization_id, quotation_id, user.id,
        change_reason=f"Version snapshot prior to counter-discount application: {payload.change_reason}"
    )

    if payload.quotation_item_id:
        item = next((i for i in quotation.items if i.id == payload.quotation_item_id), None)
        if not item:
            raise NotFoundException("Specified quotation line item was not found")

        disc_pct = round_decimal(payload.requested_discount_percent)
        item.discount_percent = disc_pct
        base_total = round_decimal(item.quantity * item.unit_price)
        item.discount_amount = round_decimal(base_total * (disc_pct / Decimal("100.00")))
        item.line_total = round_decimal(base_total - item.discount_amount + item.tax_amount)
    else:
        # Apply discount to all items
        disc_pct = round_decimal(payload.requested_discount_percent)
        for item in quotation.items:
            item.discount_percent = disc_pct
            base_total = round_decimal(item.quantity * item.unit_price)
            item.discount_amount = round_decimal(base_total * (disc_pct / Decimal("100.00")))
            item.line_total = round_decimal(base_total - item.discount_amount + item.tax_amount)

    # Recalculate totals
    new_subtotal = round_decimal(sum((i.line_total for i in quotation.items), Decimal("0.00")))
    quotation.subtotal = new_subtotal
    quotation.total_amount = round_decimal(new_subtotal - quotation.discount_amount + quotation.tax_amount)
    quotation.updated_by_user_id = user.id

    # If quotation status is sent, revert back to draft/priced for re-approval
    if quotation.status == "sent":
        quotation.status = "priced"

    # Invalidate approval
    await approval_engine.invalidate_quotation_approval(
        db=db,
        organization_id=organization_id,
        quotation_id=quotation_id,
        actor_user_id=user.id,
        actor_name=user.full_name,
        reason=f"Approval invalidated due to counter-discount edit: {payload.change_reason}"
    )

    await db.flush()

    # Create new snapshot AFTER applying changes
    await create_quotation_version_snapshot(
        db, organization_id, quotation_id, user.id,
        change_reason=f"Applied counter-discount ({payload.requested_discount_percent}%): {payload.change_reason}"
    )

    return await quotation_service.get_quotation_by_id(db, organization_id, quotation_id)


# --- 3. Quotation Version Snapshots ---

async def create_quotation_version_snapshot(
    db: AsyncSession,
    organization_id: uuid.UUID,
    quotation_id: uuid.UUID,
    created_by_user_id: Optional[uuid.UUID] = None,
    change_reason: str = "Version snapshot"
) -> QuotationVersion:
    """Captures an immutable version snapshot of quotation commercial parameters."""
    quotation = await quotation_service.get_quotation_by_id(db, organization_id, quotation_id)

    # Calculate version number
    stmt = (
        select(func.coalesce(func.max(QuotationVersion.version_number), 0))
        .where(
            QuotationVersion.organization_id == organization_id,
            QuotationVersion.quotation_id == quotation_id
        )
    )
    res = await db.execute(stmt)
    current_max = res.scalar() or 0
    next_ver = current_max + 1

    payload_items = []
    total_cost = Decimal("0.00")
    for item in quotation.items:
        payload_items.append({
            "item_id": str(item.id),
            "product_id": str(item.product_id),
            "product_name": item.product_name,
            "sku": item.sku,
            "quantity": str(item.quantity),
            "unit_price": str(item.unit_price),
            "unit_cost": str(item.unit_cost or 0),
            "discount_percent": str(item.discount_percent),
            "discount_amount": str(item.discount_amount),
            "tax_amount": str(item.tax_amount),
            "line_total": str(item.line_total)
        })
        total_cost += round_decimal((item.unit_cost or Decimal("0.00")) * item.quantity)

    gross_margin = round_decimal(quotation.subtotal - total_cost)
    margin_pct = round_decimal((gross_margin / quotation.subtotal * Decimal("100.00"))) if quotation.subtotal > Decimal("0.00") else Decimal("0.00")

    snapshot = {
        "quotation_id": str(quotation.id),
        "quotation_number": quotation.quotation_number,
        "status": quotation.status,
        "subtotal": str(quotation.subtotal),
        "discount_amount": str(quotation.discount_amount),
        "tax_amount": str(quotation.tax_amount),
        "total_amount": str(quotation.total_amount),
        "items": payload_items
    }

    qv = QuotationVersion(
        organization_id=organization_id,
        quotation_id=quotation_id,
        version_number=next_ver,
        subtotal=quotation.subtotal,
        discount_amount=quotation.discount_amount,
        tax_amount=quotation.tax_amount,
        total_amount=quotation.total_amount,
        gross_margin=gross_margin,
        margin_percent=margin_pct,
        change_reason=change_reason,
        snapshot_payload=snapshot,
        created_by_user_id=created_by_user_id,
        created_at=datetime.now(timezone.utc)
    )

    db.add(qv)
    await db.flush()
    return qv


async def list_quotation_versions(
    db: AsyncSession,
    organization_id: uuid.UUID,
    quotation_id: uuid.UUID
) -> List[QuotationVersion]:
    """Lists historical versions for a quotation."""
    stmt = (
        select(QuotationVersion)
        .where(
            QuotationVersion.organization_id == organization_id,
            QuotationVersion.quotation_id == quotation_id
        )
        .order_by(QuotationVersion.version_number.desc())
    )
    res = await db.execute(stmt)
    return list(res.scalars().all())
