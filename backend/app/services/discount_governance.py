import uuid
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime, timezone
from typing import List, Optional, Tuple, Dict
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
import logging

from app.models.discount_policy import DiscountPolicy
from app.models.quotation import Quotation
from app.schemas.discount_governance import (
    DiscountPolicyCreate, DiscountPolicyUpdate, GovernanceEvaluationResult, GovernanceViolation
)
from app.services import quotations as quotation_service
from app.services import pricing as pricing_service
from app.core.exceptions import NotFoundException, BusinessRuleViolationException

logger = logging.getLogger("dealflow360.discount_governance_service")

TWO_DECIMALS = Decimal("0.01")


def round_decimal(val: Decimal) -> Decimal:
    """Rounds monetary decimal values consistently to two decimal places."""
    return val.quantize(TWO_DECIMALS, rounding=ROUND_HALF_UP)


async def create_discount_policy(
    db: AsyncSession,
    organization_id: uuid.UUID,
    payload: DiscountPolicyCreate
) -> DiscountPolicy:
    """Creates a new tenant-scoped discount policy."""
    if payload.product_id:
        await quotation_service.verify_product_in_tenant(db, organization_id, payload.product_id)
    if payload.customer_id:
        await quotation_service.verify_customer_in_tenant(db, organization_id, payload.customer_id)

    if payload.valid_from and payload.valid_until and payload.valid_until < payload.valid_from:
        raise BusinessRuleViolationException("Policy valid_until cannot be earlier than valid_from date")

    policy = DiscountPolicy(
        organization_id=organization_id,
        name=payload.name.strip(),
        description=payload.description.strip() if payload.description else None,
        is_active=payload.is_active,
        priority=payload.priority,
        scope=payload.scope.strip().lower(),
        product_id=payload.product_id,
        customer_id=payload.customer_id,
        user_id=payload.user_id,
        role=payload.role.strip().lower() if payload.role else None,
        max_discount_percent=round_decimal(payload.max_discount_percent) if payload.max_discount_percent is not None else None,
        max_discount_amount=round_decimal(payload.max_discount_amount) if payload.max_discount_amount is not None else None,
        minimum_unit_price=round_decimal(payload.minimum_unit_price) if payload.minimum_unit_price is not None else None,
        minimum_margin_percent=round_decimal(payload.minimum_margin_percent) if payload.minimum_margin_percent is not None else None,
        valid_from=payload.valid_from,
        valid_until=payload.valid_until
    )

    try:
        db.add(policy)
        await db.flush()
    except IntegrityError:
        await db.rollback()
        raise BusinessRuleViolationException("Discount policy creation failed due to database constraint violation.")

    return await get_discount_policy_by_id(db, organization_id, policy.id)


async def list_discount_policies(
    db: AsyncSession,
    organization_id: uuid.UUID,
    skip: int = 0,
    limit: int = 100,
    scope: Optional[str] = None,
    is_active: Optional[bool] = None,
    product_id: Optional[uuid.UUID] = None,
    customer_id: Optional[uuid.UUID] = None
) -> List[DiscountPolicy]:
    """Retrieves discount policies scoped strictly to the organization."""
    stmt = select(DiscountPolicy).where(DiscountPolicy.organization_id == organization_id)

    if scope:
        stmt = stmt.where(DiscountPolicy.scope == scope.strip().lower())
    if is_active is not None:
        stmt = stmt.where(DiscountPolicy.is_active == is_active)
    if product_id:
        stmt = stmt.where(DiscountPolicy.product_id == product_id)
    if customer_id:
        stmt = stmt.where(DiscountPolicy.customer_id == customer_id)

    stmt = stmt.order_by(DiscountPolicy.priority.asc(), DiscountPolicy.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_discount_policy_by_id(
    db: AsyncSession,
    organization_id: uuid.UUID,
    policy_id: uuid.UUID
) -> DiscountPolicy:
    """Gets a specific discount policy within tenant scope."""
    stmt = select(DiscountPolicy).where(
        DiscountPolicy.id == policy_id,
        DiscountPolicy.organization_id == organization_id
    )
    result = await db.execute(stmt)
    policy = result.scalar_one_or_none()
    if not policy:
        raise NotFoundException("Discount policy requested was not found")
    return policy


async def update_discount_policy(
    db: AsyncSession,
    organization_id: uuid.UUID,
    policy_id: uuid.UUID,
    payload: DiscountPolicyUpdate
) -> DiscountPolicy:
    """Updates an existing discount policy."""
    policy = await get_discount_policy_by_id(db, organization_id, policy_id)
    data = payload.model_dump(exclude_unset=True)

    if "name" in data and data["name"] is not None:
        policy.name = data["name"].strip()
    if "description" in data:
        policy.description = data["description"].strip() if data["description"] else None
    if "is_active" in data and data["is_active"] is not None:
        policy.is_active = data["is_active"]
    if "priority" in data and data["priority"] is not None:
        policy.priority = data["priority"]
    if "scope" in data and data["scope"] is not None:
        policy.scope = data["scope"].strip().lower()
    if "max_discount_percent" in data:
        policy.max_discount_percent = round_decimal(data["max_discount_percent"]) if data["max_discount_percent"] is not None else None
    if "max_discount_amount" in data:
        policy.max_discount_amount = round_decimal(data["max_discount_amount"]) if data["max_discount_amount"] is not None else None
    if "minimum_unit_price" in data:
        policy.minimum_unit_price = round_decimal(data["minimum_unit_price"]) if data["minimum_unit_price"] is not None else None
    if "minimum_margin_percent" in data:
        policy.minimum_margin_percent = round_decimal(data["minimum_margin_percent"]) if data["minimum_margin_percent"] is not None else None
    if "valid_from" in data:
        policy.valid_from = data["valid_from"]
    if "valid_until" in data:
        policy.valid_until = data["valid_until"]

    if policy.valid_from and policy.valid_until and policy.valid_until < policy.valid_from:
        raise BusinessRuleViolationException("Policy valid_until cannot be earlier than valid_from date")

    try:
        await db.flush()
    except IntegrityError:
        await db.rollback()
        raise BusinessRuleViolationException("Discount policy update failed due to database constraint violation.")

    return await get_discount_policy_by_id(db, organization_id, policy.id)


async def delete_discount_policy(
    db: AsyncSession,
    organization_id: uuid.UUID,
    policy_id: uuid.UUID
) -> None:
    """Deletes a discount policy within tenant scope."""
    policy = await get_discount_policy_by_id(db, organization_id, policy_id)
    await db.delete(policy)
    await db.flush()


SCOPE_RANK = {
    "user": 5,
    "customer": 4,
    "product": 3,
    "role": 2,
    "organization": 1,
}


async def evaluate_discount_governance(
    db: AsyncSession,
    organization_id: uuid.UUID,
    quotation_id: Optional[uuid.UUID] = None,
    customer_id: Optional[uuid.UUID] = None,
    user_id: Optional[uuid.UUID] = None,
    user_role: Optional[str] = None,
    items_data: Optional[List[Dict]] = None
) -> GovernanceEvaluationResult:
    """
    Evaluates discount compliance against active policies for a quotation or preview items.
    Checks requested discount %, min unit price, and min margin %.
    """
    now = datetime.now(timezone.utc)

    # 1. Fetch matching active policies for organization
    stmt = select(DiscountPolicy).where(
        DiscountPolicy.organization_id == organization_id,
        DiscountPolicy.is_active == True,
        or_(DiscountPolicy.valid_from == None, DiscountPolicy.valid_from <= now),
        or_(DiscountPolicy.valid_until == None, DiscountPolicy.valid_until >= now)
    )
    result = await db.execute(stmt)
    all_policies = list(result.scalars().all())

    # 2. Extract items to evaluate
    eval_items = []
    target_customer_id = customer_id

    if quotation_id:
        quotation = await quotation_service.get_quotation_by_id(db, organization_id, quotation_id)
        target_customer_id = quotation.customer_id
        for item in quotation.items:
            base_p = round_decimal(item.unit_price) # unit selling price
            eval_items.append({
                "product_id": item.product_id,
                "product_name": item.product_name,
                "quantity": item.quantity,
                "unit_price": item.unit_price,
                "unit_cost": item.unit_cost,
                "discount_percent": item.discount_percent,
                "discount_amount": item.discount_amount,
                "line_total": item.line_total
            })
    elif items_data:
        for item in items_data:
            eval_items.append({
                "product_id": item.get("product_id"),
                "product_name": item.get("product_name", "Product"),
                "quantity": Decimal(str(item.get("quantity", "1"))),
                "unit_price": Decimal(str(item.get("unit_price", "0.00"))),
                "unit_cost": Decimal(str(item.get("unit_cost", "0.00"))),
                "discount_percent": Decimal(str(item.get("discount_percent", "0.00"))),
                "discount_amount": Decimal(str(item.get("discount_amount", "0.00"))),
                "line_total": Decimal(str(item.get("line_total", "0.00")))
            })

    if not all_policies:
        # Calculate blended discount for report
        tot_disc = sum((i["discount_amount"] for i in eval_items), Decimal("0.00"))
        tot_rev = sum((i["line_total"] for i in eval_items), Decimal("0.00"))
        gross_base = tot_rev + tot_disc
        blended_pct = round_decimal((tot_disc / gross_base * Decimal("100.00")) if gross_base > Decimal("0.00") else Decimal("0.00"))

        return GovernanceEvaluationResult(
            compliant=True,
            status="NO_POLICY",
            blended_discount_percent=blended_pct,
            applied_policies_count=0,
            violations=[],
            explanation="No active discount governance policies configured for organization."
        )

    violations: List[GovernanceViolation] = []
    applied_count = 0

    # Total discount and revenue metrics
    tot_disc = sum((i["discount_amount"] for i in eval_items), Decimal("0.00"))
    tot_rev = sum((i["line_total"] for i in eval_items), Decimal("0.00"))
    gross_base = tot_rev + tot_disc
    blended_pct = round_decimal((tot_disc / gross_base * Decimal("100.00")) if gross_base > Decimal("0.00") else Decimal("0.00"))

    # Evaluate each item against relevant matching policies
    for item in eval_items:
        prod_id = item["product_id"]

        # Filter policies matching scope criteria for this item
        matching = []
        for pol in all_policies:
            if pol.scope == "user" and pol.user_id and pol.user_id != user_id:
                continue
            if pol.scope == "customer" and pol.customer_id and pol.customer_id != target_customer_id:
                continue
            if pol.scope == "product" and pol.product_id and pol.product_id != prod_id:
                continue
            if pol.scope == "role" and pol.role and pol.role != user_role:
                continue
            matching.append(pol)

        if not matching:
            continue

        # Sort matching policies by scope rank (highest first) then priority (1 = highest first)
        matching.sort(key=lambda p: (SCOPE_RANK.get(p.scope, 0), -p.priority), reverse=True)
        active_policy = matching[0]
        applied_count += 1

        req_disc_pct = item["discount_percent"]
        actual_price = item["unit_price"]
        unit_cost = item["unit_cost"]
        line_rev = item["line_total"]
        line_cost = round_decimal(item["quantity"] * unit_cost)
        line_margin = round_decimal(line_rev - line_cost)
        margin_pct = round_decimal((line_margin / line_rev * Decimal("100.00")) if line_rev > Decimal("0.00") else Decimal("-100.00"))

        # Check 1: Max discount percent
        if active_policy.max_discount_percent is not None and req_disc_pct > active_policy.max_discount_percent:
            violations.append(GovernanceViolation(
                rule_id=active_policy.id,
                rule_name=active_policy.name,
                violation_type="MAX_DISCOUNT_PERCENT",
                message=f"Discount {req_disc_pct}% on '{item['product_name']}' exceeds policy limit of {active_policy.max_discount_percent}%.",
                product_id=prod_id,
                product_name=item['product_name'],
                requested_val=f"{req_disc_pct}%",
                policy_limit_val=f"{active_policy.max_discount_percent}%"
            ))

        # Check 2: Minimum unit price
        if active_policy.minimum_unit_price is not None and actual_price < active_policy.minimum_unit_price:
            violations.append(GovernanceViolation(
                rule_id=active_policy.id,
                rule_name=active_policy.name,
                violation_type="MINIMUM_UNIT_PRICE",
                message=f"Unit selling price ${actual_price} on '{item['product_name']}' is below policy minimum of ${active_policy.minimum_unit_price}.",
                product_id=prod_id,
                product_name=item['product_name'],
                requested_val=f"${actual_price}",
                policy_limit_val=f"${active_policy.minimum_unit_price}"
            ))

        # Check 3: Minimum margin percent
        if active_policy.minimum_margin_percent is not None and margin_pct < active_policy.minimum_margin_percent:
            violations.append(GovernanceViolation(
                rule_id=active_policy.id,
                rule_name=active_policy.name,
                violation_type="MINIMUM_MARGIN_PERCENT",
                message=f"Line margin {margin_pct}% on '{item['product_name']}' is below policy minimum margin of {active_policy.minimum_margin_percent}%.",
                product_id=prod_id,
                product_name=item['product_name'],
                requested_val=f"{margin_pct}%",
                policy_limit_val=f"{active_policy.minimum_margin_percent}%"
            ))

    compliant = len(violations) == 0
    status = "WITHIN_POLICY" if compliant else "OUTSIDE_POLICY"
    explanation = (
        f"Governance evaluation complete: {status} ({applied_count} policies evaluated, {len(violations)} violations detected)."
    )

    return GovernanceEvaluationResult(
        compliant=compliant,
        status=status,
        blended_discount_percent=blended_pct,
        applied_policies_count=applied_count,
        violations=violations,
        explanation=explanation
    )
