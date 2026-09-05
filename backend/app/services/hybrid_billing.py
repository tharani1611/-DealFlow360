import uuid
from decimal import Decimal
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.fulfillment import BillingClassification
from app.models.quotation import Quotation, QuotationItem
from app.models.product import Product
from app.schemas.inventory import LineBillingClassification, BillingClassificationResponse
from app.core.exceptions import NotFoundException


async def classify_quotation_hybrid_billing(
    session: AsyncSession,
    organization_id: uuid.UUID,
    quotation_id: uuid.UUID,
) -> BillingClassificationResponse:
    """Classify quotation lines into physical products (ONE_TIME) vs. recurring subscription plans (RECURRING) and assign commercial model (ONE_TIME, RECURRING, HYBRID)."""
    q_stmt = select(Quotation).where(Quotation.id == quotation_id, Quotation.organization_id == organization_id)
    q_res = await session.execute(q_stmt)
    quotation = q_res.scalar_one_or_none()
    if not quotation:
        raise NotFoundException(f"Quotation {quotation_id} not found")

    items_stmt = select(QuotationItem).where(QuotationItem.quotation_id == quotation_id)
    items = list((await session.execute(items_stmt)).scalars().all())

    line_classifications: List[LineBillingClassification] = []
    one_time_total = Decimal("0.00")
    recurring_total = Decimal("0.00")

    for item in items:
        prod_stmt = select(Product).where(Product.id == item.product_id)
        prod = (await session.execute(prod_stmt)).scalar_one_or_none()
        prod_name = prod.name if prod else "Item"

        # Subscription plan or recurring product heuristic
        is_recurring = any(keyword in prod_name.lower() for keyword in ["subscription", "monthly", "recurring", "saas", "plan", "annual", "license"])
        billing_type = "RECURRING" if is_recurring else "ONE_TIME"

        line_cls = LineBillingClassification(
            quotation_item_id=item.id,
            product_id=item.product_id,
            product_name=prod_name,
            billing_type=billing_type,
            unit_price=item.unit_price,
            quantity=item.quantity,
            line_total=item.line_total,
        )
        line_classifications.append(line_cls)

        if billing_type == "ONE_TIME":
            one_time_total += item.line_total
        else:
            recurring_total += item.line_total

    if one_time_total > Decimal("0.00") and recurring_total > Decimal("0.00"):
        commercial_model = "HYBRID"
    elif recurring_total > Decimal("0.00"):
        commercial_model = "RECURRING"
    else:
        commercial_model = "ONE_TIME"

    # Persist or update BillingClassification record
    stmt = select(BillingClassification).where(
        BillingClassification.organization_id == organization_id,
        BillingClassification.quotation_id == quotation_id,
    )
    b_class = (await session.execute(stmt)).scalar_one_or_none()

    json_lines = [l.model_dump(mode="json") for l in line_classifications]

    if not b_class:
        b_class = BillingClassification(
            organization_id=organization_id,
            quotation_id=quotation_id,
            commercial_model=commercial_model,
            one_time_total=one_time_total,
            recurring_monthly_total=recurring_total,
            billing_frequency="MONTHLY",
            line_classifications=json_lines,
        )
        session.add(b_class)
    else:
        b_class.commercial_model = commercial_model
        b_class.one_time_total = one_time_total
        b_class.recurring_monthly_total = recurring_total
        b_class.line_classifications = json_lines

    await session.commit()
    await session.refresh(b_class)

    return BillingClassificationResponse(
        id=b_class.id,
        organization_id=b_class.organization_id,
        quotation_id=b_class.quotation_id,
        commercial_model=commercial_model,
        one_time_total=one_time_total,
        recurring_monthly_total=recurring_total,
        billing_frequency=b_class.billing_frequency,
        line_classifications=line_classifications,
        created_at=b_class.created_at,
    )
