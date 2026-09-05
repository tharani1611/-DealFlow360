import uuid
from typing import List
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.portal_user import PortalUser
from app.models.quotation import Quotation
from app.schemas.portal import PortalQuotationDetailResponse, PortalQuotationItemResponse, PortalQuotationListItemResponse, PortalActionResponse
from app.services import quotation_state
from app.core.exceptions import NotFoundException, BusinessRuleViolationException


async def list_portal_quotations(
    db: AsyncSession,
    portal_user: PortalUser
) -> List[PortalQuotationListItemResponse]:
    """Lists quotations for the portal user's customer and organization."""
    stmt = (
        select(Quotation)
        .where(
            Quotation.organization_id == portal_user.organization_id,
            Quotation.customer_id == portal_user.customer_id,
            Quotation.status.in_(["sent", "accepted", "rejected", "expired", "converted"])
        )
        .order_by(Quotation.created_at.desc())
    )
    res = await db.execute(stmt)
    quotations = res.scalars().all()

    return [
        PortalQuotationListItemResponse(
            id=q.id,
            quotation_number=q.quotation_number,
            status=q.status,
            issue_date=q.issue_date,
            expiration_date=q.valid_until,
            total_amount=q.total_amount,
            currency=q.currency or "USD",
            created_at=q.created_at
        )
        for q in quotations
    ]


async def get_portal_quotation_detail(
    db: AsyncSession,
    portal_user: PortalUser,
    quotation_id: uuid.UUID
) -> PortalQuotationDetailResponse:
    """Retrieves single quotation detail for portal user with STRICT customer isolation and sanitized payload."""
    stmt = (
        select(Quotation)
        .options(
            selectinload(Quotation.customer),
            selectinload(Quotation.items)
        )
        .where(
            Quotation.id == quotation_id,
            Quotation.organization_id == portal_user.organization_id,
            Quotation.customer_id == portal_user.customer_id
        )
    )
    res = await db.execute(stmt)
    quotation = res.scalar_one_or_none()

    if not quotation or quotation.status not in ("sent", "accepted", "rejected", "expired", "converted"):
        raise NotFoundException("Quotation not found or not accessible")

    items_res = []
    for item in quotation.items:
        product_name = item.product_name or (item.product.name if hasattr(item, 'product') and item.product else item.description)
        sku = item.sku or (item.product.sku if hasattr(item, 'product') and item.product else None)
        items_res.append(
            PortalQuotationItemResponse(
                id=item.id,
                product_id=item.product_id,
                product_name=product_name,
                sku=sku,
                quantity=item.quantity,
                unit_price=item.unit_price,
                discount_percent=item.discount_percent,
                line_total=item.line_total,
                notes=item.description
            )
        )

    customer_name = quotation.customer.name if quotation.customer else None

    return PortalQuotationDetailResponse(
        id=quotation.id,
        quotation_number=quotation.quotation_number,
        customer_id=quotation.customer_id,
        customer_name=customer_name,
        status=quotation.status,
        issue_date=quotation.quotation_date,
        expiration_date=quotation.valid_until,
        subtotal=quotation.subtotal,
        discount_amount=quotation.discount_amount,
        tax_amount=quotation.tax_amount,
        total_amount=quotation.total_amount,
        currency=quotation.currency or "USD",
        notes=quotation.notes,
        items=items_res,
        created_at=quotation.created_at
    )


async def accept_portal_quotation(
    db: AsyncSession,
    portal_user: PortalUser,
    quotation_id: uuid.UUID,
    reason: str = None
) -> PortalActionResponse:
    """Customer accepts the quotation in portal."""
    detail = await get_portal_quotation_detail(db, portal_user, quotation_id)
    if detail.status != "sent":
        raise BusinessRuleViolationException(f"Cannot accept quotation in state '{detail.status}'. Must be 'sent'.")

    q = await quotation_state.transition_quotation(
        db=db,
        organization_id=portal_user.organization_id,
        quotation_id=quotation_id,
        target_status="accepted",
        reason=reason or f"Accepted by customer via portal ({portal_user.full_name})"
    )

    return PortalActionResponse(
        success=True,
        message="Quotation accepted successfully",
        quotation_id=q.id,
        status=q.status
    )


async def reject_portal_quotation(
    db: AsyncSession,
    portal_user: PortalUser,
    quotation_id: uuid.UUID,
    reason: str = None
) -> PortalActionResponse:
    """Customer rejects the quotation in portal."""
    detail = await get_portal_quotation_detail(db, portal_user, quotation_id)
    if detail.status != "sent":
        raise BusinessRuleViolationException(f"Cannot reject quotation in state '{detail.status}'. Must be 'sent'.")

    q = await quotation_state.transition_quotation(
        db=db,
        organization_id=portal_user.organization_id,
        quotation_id=quotation_id,
        target_status="rejected",
        reason=reason or f"Rejected by customer via portal ({portal_user.full_name})"
    )

    return PortalActionResponse(
        success=True,
        message="Quotation rejected successfully",
        quotation_id=q.id,
        status=q.status
    )
