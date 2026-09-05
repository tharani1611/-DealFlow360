import uuid
from decimal import Decimal, ROUND_HALF_UP
from typing import List, Optional, Dict
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.schemas.discount_risk import RiskEvaluationResult, RiskFactor
from app.schemas.discount_governance import GovernanceEvaluationResult
from app.schemas.margin import QuotationMarginResponse
from app.services import margins as margins_service
from app.services import discount_governance as governance_service

logger = logging.getLogger("dealflow360.discount_risk_service")

TWO_DECIMALS = Decimal("0.01")


def round_decimal(val: Decimal) -> Decimal:
    """Rounds monetary decimal values consistently to two decimal places."""
    return val.quantize(TWO_DECIMALS, rounding=ROUND_HALF_UP)


async def evaluate_discount_risk(
    db: AsyncSession,
    organization_id: uuid.UUID,
    quotation_id: Optional[uuid.UUID] = None,
    customer_id: Optional[uuid.UUID] = None,
    user_id: Optional[uuid.UUID] = None,
    user_role: Optional[str] = None,
    governance_res: Optional[GovernanceEvaluationResult] = None,
    margin_res: Optional[QuotationMarginResponse] = None,
    items_data: Optional[List[Dict]] = None
) -> RiskEvaluationResult:
    """
    Evaluates commercial risk using blended discount %, margin profitability, manual price overrides, and governance policy violations.
    Produces a deterministic score (0-100) and classification (LOW, MEDIUM, HIGH, CRITICAL).
    """
    # 1. Resolve Margin Engine results if not provided
    if margin_res is None:
        if quotation_id:
            margin_res = await margins_service.get_quotation_margin(db, organization_id, quotation_id)
        elif items_data and customer_id:
            from app.schemas.margin import MarginCalculateRequest, MarginItemInput
            margin_req = MarginCalculateRequest(
                customer_id=customer_id,
                items=[
                    MarginItemInput(
                        product_id=item.get("product_id"),
                        quantity=Decimal(str(item.get("quantity", "1"))),
                        manual_unit_price=Decimal(str(item.get("unit_price"))) if item.get("unit_price") is not None else None,
                        manual_unit_cost=Decimal(str(item.get("unit_cost"))) if item.get("unit_cost") is not None else None
                    ) for item in items_data
                ]
            )
            margin_res = await margins_service.calculate_margin_preview(db, organization_id, margin_req)

    # 2. Resolve Governance Engine results if not provided
    if governance_res is None:
        governance_res = await governance_service.evaluate_discount_governance(
            db, organization_id, quotation_id=quotation_id, customer_id=customer_id, user_id=user_id, user_role=user_role, items_data=items_data
        )

    # 3. Calculate Revenue-Weighted Blended Discount Percentage
    blended_disc_pct = governance_res.blended_discount_percent if governance_res else Decimal("0.00")
    overall_margin_pct = margin_res.margin_percent if margin_res else Decimal("0.00")
    has_negative_margin = margin_res.gross_margin < Decimal("0.00") if margin_res else False
    has_policy_violation = not governance_res.compliant if governance_res else False

    # Check for manual price overrides
    has_manual_override = False
    if margin_res and margin_res.items:
        for item in margin_res.items:
            if item.pricing_source == "MANUAL_OVERRIDE":
                has_manual_override = True
                break

    risk_factors: List[RiskFactor] = []
    total_score = 0

    # Risk Factor 1: Blended Discount Severity
    if blended_disc_pct >= Decimal("30.00"):
        total_score += 40
        risk_factors.append(RiskFactor(
            code="SEVERE_BLENDED_DISCOUNT",
            title="Severe Blended Discount",
            description=f"Revenue-weighted blended discount of {blended_disc_pct}% exceeds high risk threshold (30%).",
            severity="CRITICAL",
            score_impact=40
        ))
    elif blended_disc_pct >= Decimal("20.00"):
        total_score += 25
        risk_factors.append(RiskFactor(
            code="HIGH_BLENDED_DISCOUNT",
            title="High Blended Discount",
            description=f"Revenue-weighted blended discount of {blended_disc_pct}% exceeds standard threshold (20%).",
            severity="HIGH",
            score_impact=25
        ))
    elif blended_disc_pct >= Decimal("10.00"):
        total_score += 10
        risk_factors.append(RiskFactor(
            code="MODERATE_BLENDED_DISCOUNT",
            title="Moderate Blended Discount",
            description=f"Revenue-weighted blended discount of {blended_disc_pct}% detected.",
            severity="MEDIUM",
            score_impact=10
        ))

    # Risk Factor 2: Margin Impact & Negative Margin
    if has_negative_margin:
        total_score += 50
        risk_factors.append(RiskFactor(
            code="NEGATIVE_GROSS_MARGIN",
            title="Negative Gross Margin",
            description=f"Quotation total cost exceeds revenue resulting in negative gross margin ({overall_margin_pct}%).",
            severity="CRITICAL",
            score_impact=50
        ))
    elif overall_margin_pct < Decimal("15.00"):
        total_score += 25
        risk_factors.append(RiskFactor(
            code="LOW_MARGIN_THREAT",
            title="Low Gross Margin Threat",
            description=f"Resulting gross margin of {overall_margin_pct}% is below healthy target (15%).",
            severity="HIGH",
            score_impact=25
        ))
    elif overall_margin_pct < Decimal("30.00"):
        total_score += 10
        risk_factors.append(RiskFactor(
            code="CAUTION_MARGIN",
            title="Cautionary Margin",
            description=f"Resulting gross margin of {overall_margin_pct}% is in caution range (15-30%).",
            severity="MEDIUM",
            score_impact=10
        ))

    # Risk Factor 3: Policy Violations
    if has_policy_violation:
        violation_count = len(governance_res.violations) if governance_res else 1
        total_score += 30
        risk_factors.append(RiskFactor(
            code="POLICY_VIOLATION_DETECTED",
            title="Discount Policy Violation",
            description=f"Quotation violates {violation_count} commercial discount governance policies.",
            severity="HIGH",
            score_impact=30
        ))

    # Risk Factor 4: Manual Price Override
    if has_manual_override:
        total_score += 15
        risk_factors.append(RiskFactor(
            code="MANUAL_PRICE_OVERRIDE",
            title="Manual Price Override Detected",
            description="Manual unit price overrides detected on line items bypassing standard pricing rules.",
            severity="MEDIUM",
            score_impact=15
        ))

    final_score = min(100, total_score)

    # Classify Risk Level
    if final_score >= 70 or has_negative_margin:
        risk_level = "CRITICAL"
    elif final_score >= 45 or has_policy_violation:
        risk_level = "HIGH"
    elif final_score >= 20:
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"

    explanation = (
        f"Commercial Risk: {risk_level} (Score: {final_score}/100, Blended Discount: {blended_disc_pct}%, Gross Margin: {overall_margin_pct}%, Factors: {len(risk_factors)})."
    )

    return RiskEvaluationResult(
        risk_level=risk_level,
        risk_score=final_score,
        blended_discount_percent=blended_disc_pct,
        overall_margin_percent=overall_margin_pct,
        has_negative_margin=has_negative_margin,
        has_manual_override=has_manual_override,
        has_policy_violation=has_policy_violation,
        risk_factors=risk_factors,
        explanation=explanation
    )
