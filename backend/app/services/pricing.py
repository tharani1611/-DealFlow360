import uuid
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime, timezone
from typing import List, Optional, Tuple
from sqlalchemy import select, func, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
import logging

from app.models.pricing_rule import PricingRule
from app.models.product import Product
from app.models.customer import Customer
from app.schemas.pricing import (
    PricingRuleCreate, PricingRuleUpdate, PricingCalculateRequest, PricingCalculateResponse
)
from app.services.quotations import verify_product_in_tenant, verify_customer_in_tenant
from app.core.exceptions import NotFoundException, ConflictException, BusinessRuleViolationException

logger = logging.getLogger("dealflow360.pricing_service")

TWO_DECIMALS = Decimal("0.01")


def round_decimal(val: Decimal) -> Decimal:
    """Rounds monetary decimal values consistently to two decimal places using HALF_UP rounding."""
    return val.quantize(TWO_DECIMALS, rounding=ROUND_HALF_UP)


async def create_pricing_rule(
    db: AsyncSession,
    organization_id: uuid.UUID,
    payload: PricingRuleCreate
) -> PricingRule:
    """Creates a new tenant-scoped pricing rule with validation."""
    # 1. Verify target product exists within organization
    await verify_product_in_tenant(db, organization_id, payload.product_id)

    # 2. Verify customer if specified
    if payload.customer_id:
        await verify_customer_in_tenant(db, organization_id, payload.customer_id)

    # 3. Rule type specific requirement checks
    if payload.rule_type in ("contract", "customer") and not payload.customer_id:
        raise BusinessRuleViolationException(f"Customer ID is required for rule type '{payload.rule_type}'")

    # 4. Date sanity check
    if payload.valid_from and payload.valid_until and payload.valid_until < payload.valid_from:
        raise BusinessRuleViolationException("Rule end date (valid_until) cannot be earlier than start date (valid_from)")

    # 5. Quantity range check
    if payload.max_quantity is not None and payload.max_quantity < payload.min_quantity:
        raise BusinessRuleViolationException("max_quantity cannot be less than min_quantity")

    # 6. Percentage discount range check
    if payload.price_type == "percentage_discount" and payload.value > Decimal("100.00"):
        raise BusinessRuleViolationException("Percentage discount cannot exceed 100%")

    rule = PricingRule(
        organization_id=organization_id,
        name=payload.name.strip(),
        rule_type=payload.rule_type,
        product_id=payload.product_id,
        customer_id=payload.customer_id,
        min_quantity=round_decimal(payload.min_quantity),
        max_quantity=round_decimal(payload.max_quantity) if payload.max_quantity is not None else None,
        price_type=payload.price_type,
        value=round_decimal(payload.value),
        priority=payload.priority,
        valid_from=payload.valid_from,
        valid_until=payload.valid_until,
        is_active=payload.is_active,
        description=payload.description.strip() if payload.description else None
    )

    try:
        db.add(rule)
        await db.flush()
    except IntegrityError as exc:
        await db.rollback()
        raise BusinessRuleViolationException("Pricing rule creation failed due to a database constraint violation.")

    return await get_pricing_rule_by_id(db, organization_id, rule.id)


async def list_pricing_rules(
    db: AsyncSession,
    organization_id: uuid.UUID,
    skip: int = 0,
    limit: int = 100,
    product_id: Optional[uuid.UUID] = None,
    customer_id: Optional[uuid.UUID] = None,
    rule_type: Optional[str] = None,
    is_active: Optional[bool] = None,
    search: Optional[str] = None
) -> List[PricingRule]:
    """Lists pricing rules scoped strictly to the user's organization."""
    stmt = select(PricingRule).where(PricingRule.organization_id == organization_id)

    if product_id:
        stmt = stmt.where(PricingRule.product_id == product_id)
    if customer_id:
        stmt = stmt.where(PricingRule.customer_id == customer_id)
    if rule_type:
        stmt = stmt.where(PricingRule.rule_type == rule_type.strip().lower())
    if is_active is not None:
        stmt = stmt.where(PricingRule.is_active == is_active)
    if search:
        pattern = f"%{search.strip()}%"
        stmt = stmt.where(or_(PricingRule.name.ilike(pattern), PricingRule.description.ilike(pattern)))

    stmt = stmt.order_by(PricingRule.priority.asc(), PricingRule.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_pricing_rule_by_id(
    db: AsyncSession,
    organization_id: uuid.UUID,
    rule_id: uuid.UUID
) -> PricingRule:
    """Gets a specific pricing rule by ID within tenant scope (raises 404 if missing or cross-tenant)."""
    stmt = select(PricingRule).where(
        PricingRule.id == rule_id,
        PricingRule.organization_id == organization_id
    )
    result = await db.execute(stmt)
    rule = result.scalar_one_or_none()
    if not rule:
        raise NotFoundException("Pricing rule requested was not found")
    return rule


async def update_pricing_rule(
    db: AsyncSession,
    organization_id: uuid.UUID,
    rule_id: uuid.UUID,
    payload: PricingRuleUpdate
) -> PricingRule:
    """Updates an existing pricing rule within tenant scope."""
    rule = await get_pricing_rule_by_id(db, organization_id, rule_id)
    update_data = payload.model_dump(exclude_unset=True)

    if "product_id" in update_data and update_data["product_id"] is not None:
        await verify_product_in_tenant(db, organization_id, update_data["product_id"])
        rule.product_id = update_data["product_id"]

    if "customer_id" in update_data:
        if update_data["customer_id"] is not None:
            await verify_customer_in_tenant(db, organization_id, update_data["customer_id"])
        rule.customer_id = update_data["customer_id"]

    target_rule_type = update_data.get("rule_type", rule.rule_type)
    target_customer_id = update_data.get("customer_id", rule.customer_id)
    if target_rule_type in ("contract", "customer") and not target_customer_id:
        raise BusinessRuleViolationException(f"Customer ID is required for rule type '{target_rule_type}'")

    if "name" in update_data and update_data["name"] is not None:
        rule.name = update_data["name"].strip()
    if "rule_type" in update_data and update_data["rule_type"] is not None:
        rule.rule_type = update_data["rule_type"]
    if "min_quantity" in update_data and update_data["min_quantity"] is not None:
        rule.min_quantity = round_decimal(update_data["min_quantity"])
    if "max_quantity" in update_data:
        rule.max_quantity = round_decimal(update_data["max_quantity"]) if update_data["max_quantity"] is not None else None
    if "price_type" in update_data and update_data["price_type"] is not None:
        rule.price_type = update_data["price_type"]
    if "value" in update_data and update_data["value"] is not None:
        rule.value = round_decimal(update_data["value"])
    if "priority" in update_data and update_data["priority"] is not None:
        rule.priority = update_data["priority"]
    if "valid_from" in update_data:
        rule.valid_from = update_data["valid_from"]
    if "valid_until" in update_data:
        rule.valid_until = update_data["valid_until"]
    if "is_active" in update_data and update_data["is_active"] is not None:
        rule.is_active = update_data["is_active"]
    if "description" in update_data:
        rule.description = update_data["description"].strip() if update_data["description"] else None

    # Sanity checks
    if rule.valid_from and rule.valid_until and rule.valid_until < rule.valid_from:
        raise BusinessRuleViolationException("Rule end date (valid_until) cannot be earlier than start date (valid_from)")

    if rule.max_quantity is not None and rule.max_quantity < rule.min_quantity:
        raise BusinessRuleViolationException("max_quantity cannot be less than min_quantity")

    if rule.price_type == "percentage_discount" and rule.value > Decimal("100.00"):
        raise BusinessRuleViolationException("Percentage discount cannot exceed 100%")

    try:
        await db.flush()
    except IntegrityError:
        await db.rollback()
        raise BusinessRuleViolationException("Pricing rule update failed due to a database constraint violation.")

    return await get_pricing_rule_by_id(db, organization_id, rule.id)


async def delete_pricing_rule(
    db: AsyncSession,
    organization_id: uuid.UUID,
    rule_id: uuid.UUID
) -> None:
    """Deletes a pricing rule within tenant scope."""
    rule = await get_pricing_rule_by_id(db, organization_id, rule_id)
    await db.delete(rule)
    await db.flush()


async def calculate_item_price(
    db: AsyncSession,
    organization_id: uuid.UUID,
    req: PricingCalculateRequest
) -> PricingCalculateResponse:
    """
    Core Deterministic Pricing Engine Pipeline.
    Evaluates Base Product Price, Customer/Contract Price, Volume Tiers, and Promotions with Precedence.
    """
    if req.quantity <= Decimal("0.00"):
        raise BusinessRuleViolationException("Quantity must be greater than zero for pricing calculation")

    # 1. Verify target product is active and belongs to tenant
    product = await verify_product_in_tenant(db, organization_id, req.product_id)
    base_price = round_decimal(product.unit_price)

    # 2. Verify customer if provided
    if req.customer_id:
        await verify_customer_in_tenant(db, organization_id, req.customer_id)

    # 3. Manual Unit Price Override Check
    if req.manual_unit_price is not None:
        if req.manual_unit_price < Decimal("0.00"):
            raise BusinessRuleViolationException("Manual unit price cannot be negative")
        final_price = round_decimal(req.manual_unit_price)
        disc_amt = max(Decimal("0.00"), base_price - final_price)
        disc_pct = round_decimal((disc_amt / base_price * Decimal("100.00")) if base_price > Decimal("0.00") else Decimal("0.00"))
        return PricingCalculateResponse(
            base_price=base_price,
            selected_unit_price=final_price,
            final_unit_price=final_price,
            quantity=round_decimal(req.quantity),
            currency=product.currency,
            pricing_source="MANUAL_OVERRIDE",
            applied_rule_id=None,
            applied_rule_name=None,
            discount_amount=disc_amt,
            discount_percent=disc_pct,
            explanation=f"Manual unit price override applied: {final_price} {product.currency} (Base price: {base_price})"
        )

    quot_date = req.quotation_date or datetime.now(timezone.utc)

    # 4. Query matching pricing rules for organization and product
    stmt = select(PricingRule).where(
        PricingRule.organization_id == organization_id,
        PricingRule.product_id == req.product_id,
        PricingRule.is_active == True,
        PricingRule.min_quantity <= req.quantity,
        or_(PricingRule.max_quantity == None, PricingRule.max_quantity >= req.quantity),
        or_(PricingRule.valid_from == None, PricingRule.valid_from <= quot_date),
        or_(PricingRule.valid_until == None, PricingRule.valid_until >= quot_date),
        or_(PricingRule.customer_id == None, PricingRule.customer_id == req.customer_id)
    ).order_by(PricingRule.priority.asc(), PricingRule.min_quantity.desc(), PricingRule.created_at.asc())

    result = await db.execute(stmt)
    matching_rules = list(result.scalars().all())

    # 5. Deterministic Precedence Resolution Pipeline:
    # Tier 1: Price Replacement Rules (override_price)
    # Order of Precedence: Contract > Customer > Volume Tier
    replacement_rule: Optional[PricingRule] = None

    # First look for matching contract or customer rules for this specific customer
    if req.customer_id:
        contract_rules = [r for r in matching_rules if r.price_type == "override_price" and r.rule_type in ("contract", "customer") and r.customer_id == req.customer_id]
        if contract_rules:
            replacement_rule = contract_rules[0]

    # If no contract/customer rule matched, check for volume replacement rules
    if replacement_rule is None:
        volume_rules = [r for r in matching_rules if r.price_type == "override_price" and r.rule_type == "volume"]
        if volume_rules:
            replacement_rule = volume_rules[0]

    # Calculate selected unit price after Tier 1 replacement
    if replacement_rule is not None:
        selected_unit_price = round_decimal(replacement_rule.value)
        source = replacement_rule.rule_type.upper()
        primary_rule = replacement_rule
    else:
        selected_unit_price = base_price
        source = "BASE_PRODUCT_PRICE"
        primary_rule = None

    # Tier 2: Price Adjustment Rules (Promotions / Additional Discounts)
    adjustment_rules = [r for r in matching_rules if r.price_type in ("percentage_discount", "fixed_discount") or r.rule_type == "promotion"]
    applied_adj_rule: Optional[PricingRule] = None

    promo_discount = Decimal("0.00")
    if adjustment_rules:
        applied_adj_rule = adjustment_rules[0]
        if applied_adj_rule.price_type == "percentage_discount":
            promo_discount = round_decimal(selected_unit_price * (applied_adj_rule.value / Decimal("100.00")))
        elif applied_adj_rule.price_type == "fixed_discount":
            promo_discount = round_decimal(applied_adj_rule.value)
        elif applied_adj_rule.price_type == "override_price":
            # Promotion that replaces price directly
            promo_discount = max(Decimal("0.00"), selected_unit_price - round_decimal(applied_adj_rule.value))

    final_unit_price = max(Decimal("0.00"), round_decimal(selected_unit_price - promo_discount))

    if promo_discount > Decimal("0.00") and source in ("BASE_PRODUCT_PRICE", "VOLUME"):
        source = "PROMOTION"
        if primary_rule is None:
            primary_rule = applied_adj_rule

    # 6. Overall Discount & Explanation Calculation
    unit_discount = max(Decimal("0.00"), base_price - final_unit_price)
    disc_pct = round_decimal((unit_discount / base_price * Decimal("100.00")) if base_price > Decimal("0.00") else Decimal("0.00"))

    if source == "BASE_PRODUCT_PRICE":
        explanation = f"Base product price applied: {base_price} {product.currency}"
    elif source in ("CONTRACT", "CUSTOMER"):
        explanation = f"{primary_rule.rule_type.capitalize()} price applied ({primary_rule.name}): {final_unit_price} {product.currency} (Base price: {base_price})"
    elif source == "VOLUME":
        explanation = f"Volume tier price applied ({primary_rule.name}, {primary_rule.min_quantity}+ units): {final_unit_price} {product.currency} (Base price: {base_price})"
    elif source == "PROMOTION":
        rule_label = primary_rule.name if primary_rule else "Promotion"
        explanation = f"Promotional price applied ({rule_label}): {final_unit_price} {product.currency} (Base price: {base_price}, {disc_pct}% discount)"
    else:
        explanation = f"Calculated price: {final_unit_price} {product.currency} (Source: {source})"

    return PricingCalculateResponse(
        base_price=base_price,
        selected_unit_price=selected_unit_price,
        final_unit_price=final_unit_price,
        quantity=round_decimal(req.quantity),
        currency=product.currency,
        pricing_source=source,
        applied_rule_id=primary_rule.id if primary_rule else None,
        applied_rule_name=primary_rule.name if primary_rule else None,
        discount_amount=unit_discount,
        discount_percent=disc_pct,
        explanation=explanation
    )
