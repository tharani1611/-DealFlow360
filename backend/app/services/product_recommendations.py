import uuid
from decimal import Decimal
from typing import List, Optional, Set, Tuple
from sqlalchemy import select, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.customer import Customer
from app.models.product import Product
from app.models.quotation import Quotation, QuotationItem
from app.models.deal import Deal
from app.models.activity import Activity
from app.models.product_recommendation_rule import ProductRecommendationRule
from app.schemas.product_recommendation import (
    ProductRecommendationRuleCreate,
    ProductRecommendationRuleUpdate,
    ProductRecommendationRuleResponse,
    ProductRecommendationItem,
    CustomerProductRecommendationsResponse,
)
from app.core.exceptions import (
    NotFoundException,
    BusinessRuleViolationException,
    ConflictException,
)


async def create_recommendation_rule(
    db: AsyncSession,
    organization_id: uuid.UUID,
    payload: ProductRecommendationRuleCreate
) -> ProductRecommendationRule:
    """Creates a new product recommendation rule with validation."""
    # 1. Self-reference check
    if payload.source_product_id == payload.target_product_id:
        raise BusinessRuleViolationException("source_product_id and target_product_id cannot be the same product.")

    # 2. Check source and target products exist in organization
    products_q = await db.execute(
        select(Product).where(
            and_(
                Product.organization_id == organization_id,
                Product.id.in_([payload.source_product_id, payload.target_product_id])
            )
        )
    )
    found_products = {p.id: p for p in products_q.scalars().all()}

    if payload.source_product_id not in found_products:
        raise NotFoundException(f"Source product '{payload.source_product_id}' not found in organization.")

    if payload.target_product_id not in found_products:
        raise NotFoundException(f"Target product '{payload.target_product_id}' not found in organization.")

    # 3. Check duplicate rule constraint
    dup_q = await db.execute(
        select(ProductRecommendationRule).where(
            and_(
                ProductRecommendationRule.organization_id == organization_id,
                ProductRecommendationRule.source_product_id == payload.source_product_id,
                ProductRecommendationRule.target_product_id == payload.target_product_id,
                ProductRecommendationRule.rule_type == payload.rule_type,
            )
        )
    )
    if dup_q.scalar_one_or_none():
        raise ConflictException(
            f"A '{payload.rule_type}' rule already exists between source product and target product."
        )

    rule = ProductRecommendationRule(
        id=uuid.uuid4(),
        organization_id=organization_id,
        source_product_id=payload.source_product_id,
        target_product_id=payload.target_product_id,
        rule_type=payload.rule_type,
        priority=payload.priority,
        is_active=payload.is_active,
        min_customer_deal_count=payload.min_customer_deal_count,
        min_customer_pipeline_value=payload.min_customer_pipeline_value,
        min_customer_activity_count=payload.min_customer_activity_count,
        description=payload.description,
    )
    db.add(rule)
    await db.commit()
    await db.refresh(rule)
    return rule


async def get_recommendation_rule(
    db: AsyncSession,
    organization_id: uuid.UUID,
    rule_id: uuid.UUID
) -> ProductRecommendationRule:
    """Retrieves a recommendation rule by ID with tenant isolation."""
    query = await db.execute(
        select(ProductRecommendationRule)
        .options(
            selectinload(ProductRecommendationRule.source_product),
            selectinload(ProductRecommendationRule.target_product),
        )
        .where(
            and_(
                ProductRecommendationRule.id == rule_id,
                ProductRecommendationRule.organization_id == organization_id
            )
        )
    )
    rule = query.scalar_one_or_none()
    if not rule:
        raise NotFoundException(f"Recommendation rule '{rule_id}' not found.")
    return rule


async def get_recommendation_rules(
    db: AsyncSession,
    organization_id: uuid.UUID,
    rule_type: Optional[str] = None,
    source_product_id: Optional[uuid.UUID] = None,
    target_product_id: Optional[uuid.UUID] = None,
    is_active: Optional[bool] = None,
    skip: int = 0,
    limit: int = 50,
) -> List[ProductRecommendationRule]:
    """Retrieves list of recommendation rules filtered by criteria."""
    filters = [ProductRecommendationRule.organization_id == organization_id]

    if rule_type:
        filters.append(ProductRecommendationRule.rule_type == rule_type)
    if source_product_id:
        filters.append(ProductRecommendationRule.source_product_id == source_product_id)
    if target_product_id:
        filters.append(ProductRecommendationRule.target_product_id == target_product_id)
    if is_active is not None:
        filters.append(ProductRecommendationRule.is_active == is_active)

    query = await db.execute(
        select(ProductRecommendationRule)
        .options(
            selectinload(ProductRecommendationRule.source_product),
            selectinload(ProductRecommendationRule.target_product),
        )
        .where(and_(*filters))
        .order_by(ProductRecommendationRule.priority.asc(), ProductRecommendationRule.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return list(query.scalars().all())


async def update_recommendation_rule(
    db: AsyncSession,
    organization_id: uuid.UUID,
    rule_id: uuid.UUID,
    payload: ProductRecommendationRuleUpdate
) -> ProductRecommendationRule:
    """Updates an existing recommendation rule."""
    rule = await get_recommendation_rule(db, organization_id, rule_id)

    if payload.priority is not None:
        rule.priority = payload.priority
    if payload.is_active is not None:
        rule.is_active = payload.is_active
    if payload.min_customer_deal_count is not None:
        rule.min_customer_deal_count = payload.min_customer_deal_count
    if payload.min_customer_pipeline_value is not None:
        rule.min_customer_pipeline_value = payload.min_customer_pipeline_value
    if payload.min_customer_activity_count is not None:
        rule.min_customer_activity_count = payload.min_customer_activity_count
    if payload.description is not None:
        rule.description = payload.description

    await db.commit()
    await db.refresh(rule)
    return rule


async def delete_recommendation_rule(
    db: AsyncSession,
    organization_id: uuid.UUID,
    rule_id: uuid.UUID
) -> None:
    """Deletes a recommendation rule."""
    rule = await get_recommendation_rule(db, organization_id, rule_id)
    await db.delete(rule)
    await db.commit()


async def get_customer_product_recommendations(
    db: AsyncSession,
    organization_id: uuid.UUID,
    customer_id: uuid.UUID
) -> CustomerProductRecommendationsResponse:
    """Evaluates deterministic Upsell & Cross-sell product recommendations for a customer."""
    # 1. Verify customer exists in organization
    cust_q = await db.execute(
        select(Customer).where(
            and_(
                Customer.id == customer_id,
                Customer.organization_id == organization_id
            )
        )
    )
    customer = cust_q.scalar_one_or_none()
    if not customer:
        raise NotFoundException(f"Customer '{customer_id}' not found.")

    # 2. Determine owned products from accepted quotations and won deals
    owned_product_ids: Set[uuid.UUID] = set()

    # Products from accepted quotations
    quote_items_q = await db.execute(
        select(QuotationItem.product_id)
        .join(Quotation, QuotationItem.quotation_id == Quotation.id)
        .where(
            and_(
                Quotation.organization_id == organization_id,
                Quotation.customer_id == customer_id,
                Quotation.status == "accepted",
                QuotationItem.product_id.isnot(None)
            )
        )
    )
    for p_id in quote_items_q.scalars().all():
        if p_id:
            owned_product_ids.add(p_id)

    # Products from won deals via quotation items
    won_deal_items_q = await db.execute(
        select(QuotationItem.product_id)
        .join(Quotation, QuotationItem.quotation_id == Quotation.id)
        .join(Deal, Deal.quotation_id == Quotation.id)
        .where(
            and_(
                Deal.organization_id == organization_id,
                Deal.customer_id == customer_id,
                Deal.status == "won",
                QuotationItem.product_id.isnot(None)
            )
        )
    )
    for p_id in won_deal_items_q.scalars().all():
        if p_id:
            owned_product_ids.add(p_id)

    if not owned_product_ids:
        return CustomerProductRecommendationsResponse(
            customer_id=customer_id,
            customer_name=customer.name,
            recommendations=[]
        )

    # 3. Calculate customer telemetry metrics for rule threshold eligibility
    won_deals_q = await db.execute(
        select(func.count(Deal.id)).where(
            and_(
                Deal.organization_id == organization_id,
                Deal.customer_id == customer_id,
                Deal.status == "won"
            )
        )
    )
    won_deal_count = won_deals_q.scalar() or 0

    open_pipe_q = await db.execute(
        select(func.coalesce(func.sum(Deal.value), 0)).where(
            and_(
                Deal.organization_id == organization_id,
                Deal.customer_id == customer_id,
                Deal.status == "open"
            )
        )
    )
    open_pipeline_val = open_pipe_q.scalar() or Decimal("0.00")

    activities_q = await db.execute(
        select(func.count(Activity.id)).where(
            and_(
                Activity.organization_id == organization_id,
                Activity.customer_id == customer_id
            )
        )
    )
    activity_count = activities_q.scalar() or 0

    # 4. Fetch active recommendation rules matching owned source products
    rules_q = await db.execute(
        select(ProductRecommendationRule)
        .options(
            selectinload(ProductRecommendationRule.source_product),
            selectinload(ProductRecommendationRule.target_product),
        )
        .where(
            and_(
                ProductRecommendationRule.organization_id == organization_id,
                ProductRecommendationRule.is_active == True,
                ProductRecommendationRule.source_product_id.in_(list(owned_product_ids))
            )
        )
        .order_by(ProductRecommendationRule.priority.asc())
    )
    rules = list(rules_q.scalars().all())

    candidate_map = {}  # target_product_id -> ProductRecommendationItem

    for rule in rules:
        src = rule.source_product
        tgt = rule.target_product

        # Skip if products inactive or if customer already owns target product
        if not src or not tgt or not src.is_active or not tgt.is_active:
            continue
        if tgt.id in owned_product_ids:
            continue

        # Evaluate threshold criteria
        eligibility_reasons = []
        if rule.min_customer_deal_count is not None:
            if won_deal_count < rule.min_customer_deal_count:
                continue
            eligibility_reasons.append(f"won deals ({won_deal_count} >= {rule.min_customer_deal_count})")

        if rule.min_customer_pipeline_value is not None:
            if open_pipeline_val < rule.min_customer_pipeline_value:
                continue
            eligibility_reasons.append(f"open pipeline (${open_pipeline_val} >= ${rule.min_customer_pipeline_value})")

        if rule.min_customer_activity_count is not None:
            if activity_count < rule.min_customer_activity_count:
                continue
            eligibility_reasons.append(f"activities ({activity_count} >= {rule.min_customer_activity_count})")

        eligibility_str = "Customer meets criteria"
        if eligibility_reasons:
            eligibility_str += ": " + ", ".join(eligibility_reasons)

        if rule.rule_type == "upsell":
            reason = f"Customer owns {src.name} and qualifies for the {tgt.name} tier upgrade."
        else:
            reason = f"Customer owns {src.name}; {tgt.name} is configured as a complementary product."

        if rule.description:
            reason += f" ({rule.description})"

        item = ProductRecommendationItem(
            product_id=tgt.id,
            product_name=tgt.name,
            sku=tgt.sku,
            unit_price=str(tgt.unit_price),
            recommendation_type=rule.rule_type,
            source_product_id=src.id,
            source_product_name=src.name,
            priority=rule.priority,
            eligibility=eligibility_str,
            reason=reason,
            rule_id=rule.id,
        )

        # Deduplicate target product: keep highest priority rule (lowest priority number)
        if tgt.id not in candidate_map or rule.priority < candidate_map[tgt.id].priority:
            candidate_map[tgt.id] = item

    # Sort final recommendations by priority asc
    recommendations = sorted(candidate_map.values(), key=lambda r: (r.priority, r.product_name))

    return CustomerProductRecommendationsResponse(
        customer_id=customer_id,
        customer_name=customer.name,
        recommendations=recommendations
    )
