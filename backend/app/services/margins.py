import uuid
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.models.quotation import Quotation, QuotationItem
from app.models.product import Product
from app.models.deal import Deal
from app.schemas.margin import (
    MarginCalculateRequest, LineMarginResponse, QuotationMarginResponse
)
from app.schemas.pricing import PricingCalculateRequest
from app.services import pricing as pricing_service
from app.services import quotations as quotation_service
from app.services import deals as deal_service
from app.core.exceptions import NotFoundException, BusinessRuleViolationException

logger = logging.getLogger("dealflow360.margins_service")

TWO_DECIMALS = Decimal("0.01")


def round_decimal(val: Decimal) -> Decimal:
    """Rounds monetary decimal values consistently to two decimal places using HALF_UP rounding."""
    return val.quantize(TWO_DECIMALS, rounding=ROUND_HALF_UP)


def classify_margin_health(margin_percent: Decimal) -> str:
    """
    Classifies margin health status based on percentage:
    >= 30.00%     -> HEALTHY
    15.00-29.99%  -> CAUTION
    0.00-14.99%   -> AT_RISK
    < 0.00%       -> NEGATIVE
    """
    if margin_percent >= Decimal("30.00"):
        return "HEALTHY"
    elif margin_percent >= Decimal("15.00"):
        return "CAUTION"
    elif margin_percent >= Decimal("0.00"):
        return "AT_RISK"
    else:
        return "NEGATIVE"


def compute_line_margin(
    product_id: uuid.UUID,
    product_name: str,
    quantity: Decimal,
    unit_selling_price: Decimal,
    unit_cost: Decimal,
    pricing_source: str = "BASE_PRODUCT_PRICE",
    currency: str = "USD"
) -> LineMarginResponse:
    """Computes line-level revenue, cost, gross margin, margin percentage, and health status."""
    qty = round_decimal(quantity)
    sell_price = round_decimal(unit_selling_price)
    cost_price = round_decimal(unit_cost)

    line_revenue = round_decimal(qty * sell_price)
    line_cost = round_decimal(qty * cost_price)
    gross_margin = round_decimal(line_revenue - line_cost)

    if line_revenue > Decimal("0.00"):
        margin_pct = round_decimal((gross_margin / line_revenue) * Decimal("100.00"))
    else:
        margin_pct = Decimal("-100.00") if gross_margin < Decimal("0.00") else Decimal("0.00")

    health_status = classify_margin_health(margin_pct)
    explanation = (
        f"{product_name}: Revenue {line_revenue} {currency} ({sell_price}/unit), "
        f"Cost {line_cost} {currency} ({cost_price}/unit), Gross Margin {gross_margin} {currency} ({margin_pct}%, {health_status})"
    )

    return LineMarginResponse(
        product_id=product_id,
        product_name=product_name,
        quantity=qty,
        unit_selling_price=sell_price,
        unit_cost=cost_price,
        line_revenue=line_revenue,
        line_cost=line_cost,
        gross_margin=gross_margin,
        margin_percent=margin_pct,
        health_status=health_status,
        pricing_source=pricing_source,
        explanation=explanation
    )


async def calculate_margin_preview(
    db: AsyncSession,
    organization_id: uuid.UUID,
    req: MarginCalculateRequest
) -> QuotationMarginResponse:
    """
    Live Margin Preview Engine.
    Invokes Phase 20 Pricing Engine to obtain final selling prices, resolves cost basis, and calculates line/quotation margins.
    """
    if not req.items:
        raise BusinessRuleViolationException("Margin calculation requires at least one line item")

    line_margins: List[LineMarginResponse] = []
    total_revenue = Decimal("0.00")
    total_cost = Decimal("0.00")

    for item_input in req.items:
        # 1. Product verification & tenant check
        product = await quotation_service.verify_product_in_tenant(db, organization_id, item_input.product_id)

        # 2. Phase 20 Pricing Engine resolution for selling price
        pricing_res = await pricing_service.calculate_item_price(
            db,
            organization_id,
            PricingCalculateRequest(
                product_id=product.id,
                quantity=item_input.quantity,
                customer_id=req.customer_id,
                quotation_date=req.quotation_date,
                currency=req.currency,
                manual_unit_price=item_input.manual_unit_price
            )
        )
        unit_selling_price = pricing_res.final_unit_price

        # 3. Unit cost resolution (manual override if specified, otherwise product.unit_cost)
        if item_input.manual_unit_cost is not None:
            if item_input.manual_unit_cost < Decimal("0.00"):
                raise BusinessRuleViolationException("Manual unit cost cannot be negative")
            unit_cost = round_decimal(item_input.manual_unit_cost)
        else:
            unit_cost = round_decimal(getattr(product, "unit_cost", Decimal("0.00")) or Decimal("0.00"))

        line_margin = compute_line_margin(
            product_id=product.id,
            product_name=product.name,
            quantity=item_input.quantity,
            unit_selling_price=unit_selling_price,
            unit_cost=unit_cost,
            pricing_source=pricing_res.pricing_source,
            currency=pricing_res.currency
        )
        line_margins.append(line_margin)
        total_revenue += line_margin.line_revenue
        total_cost += line_margin.line_cost

    total_revenue = round_decimal(total_revenue)
    total_cost = round_decimal(total_cost)
    gross_margin = round_decimal(total_revenue - total_cost)

    if total_revenue > Decimal("0.00"):
        overall_margin_pct = round_decimal((gross_margin / total_revenue) * Decimal("100.00"))
    else:
        overall_margin_pct = Decimal("-100.00") if gross_margin < Decimal("0.00") else Decimal("0.00")

    overall_health = classify_margin_health(overall_margin_pct)
    currency_code = req.currency.upper() if req.currency else "USD"
    explanation = (
        f"Quotation Preview: Total Revenue {total_revenue} {currency_code}, Total Cost {total_cost} {currency_code}, "
        f"Gross Margin {gross_margin} {currency_code} ({overall_margin_pct}%, Health: {overall_health})"
    )

    return QuotationMarginResponse(
        quotation_id=None,
        quotation_number=None,
        customer_id=req.customer_id,
        currency=currency_code,
        total_revenue=total_revenue,
        total_cost=total_cost,
        gross_margin=gross_margin,
        margin_percent=overall_margin_pct,
        health_status=overall_health,
        items=line_margins,
        explanation=explanation
    )


async def get_quotation_margin(
    db: AsyncSession,
    organization_id: uuid.UUID,
    quotation_id: uuid.UUID
) -> QuotationMarginResponse:
    """Calculates historical margin breakdown for an existing quotation using snapshotted unit costs and snapshotted unit prices."""
    quotation = await quotation_service.get_quotation_by_id(db, organization_id, quotation_id)

    line_margins: List[LineMarginResponse] = []
    total_revenue = Decimal("0.00")
    total_cost = Decimal("0.00")

    for item in quotation.items:
        line_margin = compute_line_margin(
            product_id=item.product_id,
            product_name=item.product_name,
            quantity=item.quantity,
            unit_selling_price=item.unit_price,
            unit_cost=item.unit_cost,
            pricing_source="HISTORICAL_SNAPSHOT",
            currency=quotation.currency
        )
        line_margins.append(line_margin)
        total_revenue += line_margin.line_revenue
        total_cost += line_margin.line_cost

    total_revenue = round_decimal(total_revenue)
    total_cost = round_decimal(total_cost)
    gross_margin = round_decimal(total_revenue - total_cost)

    if total_revenue > Decimal("0.00"):
        overall_margin_pct = round_decimal((gross_margin / total_revenue) * Decimal("100.00"))
    else:
        overall_margin_pct = Decimal("-100.00") if gross_margin < Decimal("0.00") else Decimal("0.00")

    overall_health = classify_margin_health(overall_margin_pct)
    explanation = (
        f"Quotation {quotation.quotation_number}: Total Revenue {total_revenue} {quotation.currency}, "
        f"Total Cost {total_cost} {quotation.currency}, Gross Margin {gross_margin} {quotation.currency} ({overall_margin_pct}%, Health: {overall_health})"
    )

    return QuotationMarginResponse(
        quotation_id=quotation.id,
        quotation_number=quotation.quotation_number,
        customer_id=quotation.customer_id,
        currency=quotation.currency,
        total_revenue=total_revenue,
        total_cost=total_cost,
        gross_margin=gross_margin,
        margin_percent=overall_margin_pct,
        health_status=overall_health,
        items=line_margins,
        explanation=explanation
    )


async def get_deal_margin(
    db: AsyncSession,
    organization_id: uuid.UUID,
    deal_id: uuid.UUID
) -> QuotationMarginResponse:
    """Calculates margin breakdown for a deal's associated quotation."""
    deal = await deal_service.get_deal_by_id(db, organization_id, deal_id)
    if not deal.quotation_id:
        raise NotFoundException("Deal does not have an associated quotation to calculate margin")
    return await get_quotation_margin(db, organization_id, deal.quotation_id)
