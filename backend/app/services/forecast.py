import uuid
from datetime import datetime, timezone, date, timedelta
from decimal import Decimal
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.deal import Deal
from app.models.customer import Customer
from app.models.quotation import Quotation
from app.models.activity import Activity
from app.schemas.forecast import (
    DealForecastItem,
    PeriodForecast,
    ForecastConfidenceFactors,
    RevenueForecastResponse
)
from app.services.intelligence import (
    calculate_deal_health,
    calculate_customer_engagement,
    calculate_pipeline_concentration
)


async def evaluate_single_deal_forecast(
    db: AsyncSession,
    organization_id: uuid.UUID,
    deal: Deal,
    customer_name: str,
    now_utc: datetime,
    today_utc: date
) -> DealForecastItem:
    """Evaluates deterministic probability adjustments, forecast category, and values for a single deal."""
    health_resp = await calculate_deal_health(db, organization_id, deal.id)
    metrics = health_resp.metrics

    base_prob = deal.probability
    adjustments = 0
    pos_factors: List[str] = []
    neg_factors: List[str] = []

    # Health score influence
    if health_resp.health_status == "healthy":
        adjustments += 15
        pos_factors.append("Healthy deal telemetry (+15%)")
    elif health_resp.health_status == "stable":
        adjustments += 5
        pos_factors.append("Stable deal telemetry (+5%)")
    elif health_resp.health_status == "at_risk":
        adjustments -= 15
        neg_factors.append("At-risk deal health status (-15%)")
    elif health_resp.health_status == "critical":
        adjustments -= 25
        neg_factors.append("Critical deal health status (-25%)")

    # Activity recency influence
    if metrics.recent_activity_count > 0:
        adjustments += 10
        pos_factors.append("Active touchpoints in the last 7 days (+10%)")
    else:
        adjustments -= 10
        neg_factors.append("No activity in the last 7 days (-10%)")

    # Overdue activities influence
    if metrics.overdue_activity_count > 0:
        penalty = min(25, metrics.overdue_activity_count * 10)
        adjustments -= penalty
        neg_factors.append(f"{metrics.overdue_activity_count} overdue follow-up item(s) (-{penalty}%)")

    # Quotation influence
    if metrics.has_accepted_quotation:
        adjustments += 15
        pos_factors.append("Commercial proposal accepted (+15%)")
    elif metrics.has_expired_or_rejected_quotation:
        adjustments -= 20
        neg_factors.append("Commercial quotation rejected or expired (-20%)")

    # Stage influence
    if deal.stage == "proposal":
        adjustments += 5
        pos_factors.append("Proposal stage alignment (+5%)")
    elif deal.stage == "negotiation":
        adjustments += 10
        pos_factors.append("Final negotiation stage (+10%)")

    created_dt = deal.created_at
    if created_dt:
        if created_dt.tzinfo is None:
            created_dt = created_dt.replace(tzinfo=timezone.utc)
        if (now_utc - created_dt).days > 30 and deal.stage == "new":
            adjustments -= 15
            neg_factors.append("Stalled in new stage for over 30 days (-15%)")

    # Imminent close date in early stage
    if metrics.days_until_expected_close is not None:
        if metrics.days_until_expected_close <= 7 and deal.stage in ("new", "qualified"):
            adjustments -= 20
            neg_factors.append(f"Closing in {metrics.days_until_expected_close} days while still in '{deal.stage}' stage (-20%)")

    # Customer engagement check
    cust_eng = await calculate_customer_engagement(db, organization_id, deal.customer_id)
    if cust_eng.is_going_cold:
        adjustments -= 10
        neg_factors.append(f"Customer relationship is cooling/cold ({cust_eng.engagement_score}/100) (-10%)")
    elif cust_eng.engagement_status == "highly_engaged":
        adjustments += 5
        pos_factors.append("Customer is highly engaged (+5%)")

    # Calculate final adjusted probability clamped to [0, 100]
    adjusted_prob = max(0, min(100, base_prob + adjustments))

    # Forecast Category Classification
    if (
        adjusted_prob >= 70 and
        health_resp.health_status in ("healthy", "stable") and
        metrics.overdue_activity_count == 0 and
        not metrics.has_expired_or_rejected_quotation
    ):
        category = "COMMITTED"
    elif (
        health_resp.health_status in ("at_risk", "critical") or
        metrics.overdue_activity_count >= 2 or
        metrics.has_expired_or_rejected_quotation or
        (metrics.days_until_expected_close is not None and metrics.days_until_expected_close <= 7 and deal.stage in ("new", "qualified")) or
        adjusted_prob < 35
    ):
        category = "AT_RISK"
    elif adjusted_prob >= 45:
        category = "UPSIDE"
    else:
        category = "PIPELINE"

    weighted_val = deal.value * Decimal(base_prob) / Decimal(100)
    forecast_val = deal.value * Decimal(adjusted_prob) / Decimal(100)

    close_date_val: Optional[date] = None
    if deal.expected_close_date:
        close_date_val = deal.expected_close_date if isinstance(deal.expected_close_date, date) else deal.expected_close_date.date()

    return DealForecastItem(
        deal_id=deal.id,
        deal_number=deal.deal_number,
        title=deal.title,
        customer_id=deal.customer_id,
        customer_name=customer_name,
        value=f"{deal.value:.2f}",
        stage=deal.stage,
        base_probability=base_prob,
        adjusted_probability=adjusted_prob,
        forecast_category=category,
        health_score=health_resp.health_score,
        health_status=health_resp.health_status,
        risk_count=len(health_resp.risk_factors),
        expected_close_date=close_date_val,
        weighted_value=f"{weighted_val:.2f}",
        forecast_value=f"{forecast_val:.2f}",
        primary_positive_factor=pos_factors[0] if pos_factors else "Standard pipeline probability",
        primary_negative_factor=neg_factors[0] if neg_factors else "No major risk factors detected",
        positive_factors=pos_factors,
        negative_factors=neg_factors
    )


async def calculate_revenue_forecast(
    db: AsyncSession,
    organization_id: uuid.UUID,
    period: Optional[str] = None,
    stage: Optional[str] = None,
    forecast_category: Optional[str] = None,
    customer_id: Optional[uuid.UUID] = None
) -> RevenueForecastResponse:
    """Calculates deterministic revenue forecast, confidence score, and time breakdown."""
    now_utc = datetime.now(timezone.utc)
    today_utc = now_utc.date()

    # Query all deals for organization
    deals_query = await db.execute(
        select(Deal, Customer.name.label("customer_name"))
        .join(Customer, Deal.customer_id == Customer.id)
        .where(Deal.organization_id == organization_id)
    )
    deal_rows = deals_query.all()

    open_deal_items: List[DealForecastItem] = []
    won_val = Decimal("0.00")
    lost_val = Decimal("0.00")

    for row in deal_rows:
        deal_obj: Deal = row[0]
        cust_name: str = row[1] or "Unknown Customer"

        if deal_obj.status == "won":
            won_val += deal_obj.value
        elif deal_obj.status == "lost":
            lost_val += deal_obj.value
        elif deal_obj.status == "open":
            item = await evaluate_single_deal_forecast(
                db, organization_id, deal_obj, cust_name, now_utc, today_utc
            )
            open_deal_items.append(item)

    # Calculate financial aggregates across all open deals
    open_pipeline_val = sum((Decimal(i.value) for i in open_deal_items), Decimal("0.00"))
    weighted_pipeline_val = sum((Decimal(i.weighted_value) for i in open_deal_items), Decimal("0.00"))
    forecast_revenue_val = sum((Decimal(i.forecast_value) for i in open_deal_items), Decimal("0.00"))
    committed_val = sum((Decimal(i.value) for i in open_deal_items if i.forecast_category == "COMMITTED"), Decimal("0.00"))
    upside_val = sum((Decimal(i.value) for i in open_deal_items if i.forecast_category == "UPSIDE"), Decimal("0.00"))
    at_risk_val = sum((Decimal(i.value) for i in open_deal_items if i.forecast_category == "AT_RISK"), Decimal("0.00"))

    # Periods calculation
    current_m = today_utc.strftime("%Y-%m")
    # Next month calculation
    next_m_date = (today_utc.replace(day=28) + timedelta(days=4)).replace(day=1)
    next_m = next_m_date.strftime("%Y-%m")

    periods_dict: Dict[str, Dict[str, Any]] = {
        "current_month": {
            "period_key": "current_month",
            "period_label": f"Current Month ({today_utc.strftime('%b %Y')})",
            "open_pipeline": Decimal("0.00"),
            "weighted_pipeline": Decimal("0.00"),
            "forecast_revenue": Decimal("0.00"),
            "committed_revenue": Decimal("0.00"),
            "upside_revenue": Decimal("0.00"),
            "at_risk_revenue": Decimal("0.00"),
            "deal_count": 0
        },
        "next_month": {
            "period_key": "next_month",
            "period_label": f"Next Month ({next_m_date.strftime('%b %Y')})",
            "open_pipeline": Decimal("0.00"),
            "weighted_pipeline": Decimal("0.00"),
            "forecast_revenue": Decimal("0.00"),
            "committed_revenue": Decimal("0.00"),
            "upside_revenue": Decimal("0.00"),
            "at_risk_revenue": Decimal("0.00"),
            "deal_count": 0
        },
        "later": {
            "period_key": "later",
            "period_label": "Later / Future Quarters",
            "open_pipeline": Decimal("0.00"),
            "weighted_pipeline": Decimal("0.00"),
            "forecast_revenue": Decimal("0.00"),
            "committed_revenue": Decimal("0.00"),
            "upside_revenue": Decimal("0.00"),
            "at_risk_revenue": Decimal("0.00"),
            "deal_count": 0
        },
        "no_close_date": {
            "period_key": "no_close_date",
            "period_label": "Unscheduled (No Close Date)",
            "open_pipeline": Decimal("0.00"),
            "weighted_pipeline": Decimal("0.00"),
            "forecast_revenue": Decimal("0.00"),
            "committed_revenue": Decimal("0.00"),
            "upside_revenue": Decimal("0.00"),
            "at_risk_revenue": Decimal("0.00"),
            "deal_count": 0
        }
    }

    for item in open_deal_items:
        val = Decimal(item.value)
        wt = Decimal(item.weighted_value)
        fc = Decimal(item.forecast_value)
        cat = item.forecast_category

        pkey = "no_close_date"
        if item.expected_close_date:
            item_m = item.expected_close_date.strftime("%Y-%m")
            if item_m == current_m:
                pkey = "current_month"
            elif item_m == next_m:
                pkey = "next_month"
            else:
                pkey = "later"

        p_target = periods_dict[pkey]
        p_target["open_pipeline"] += val
        p_target["weighted_pipeline"] += wt
        p_target["forecast_revenue"] += fc
        if cat == "COMMITTED":
            p_target["committed_revenue"] += val
        elif cat == "UPSIDE":
            p_target["upside_revenue"] += val
        elif cat == "AT_RISK":
            p_target["at_risk_revenue"] += val
        p_target["deal_count"] += 1

    periods_list: List[PeriodForecast] = []
    for key in ["current_month", "next_month", "later", "no_close_date"]:
        pdata = periods_dict[key]
        periods_list.append(PeriodForecast(
            period_key=pdata["period_key"],
            period_label=pdata["period_label"],
            open_pipeline=f"{pdata['open_pipeline']:.2f}",
            weighted_pipeline=f"{pdata['weighted_pipeline']:.2f}",
            forecast_revenue=f"{pdata['forecast_revenue']:.2f}",
            committed_revenue=f"{pdata['committed_revenue']:.2f}",
            upside_revenue=f"{pdata['upside_revenue']:.2f}",
            at_risk_revenue=f"{pdata['at_risk_revenue']:.2f}",
            deal_count=pdata["deal_count"]
        ))

    # Calculate Confidence Score (0-100) & Contributing Factors
    conf_score = 70
    conf_pos: List[str] = []
    conf_neg: List[str] = []

    if open_pipeline_val > Decimal("0.00"):
        committed_ratio = float(committed_val / open_pipeline_val)
        at_risk_ratio = float(at_risk_val / open_pipeline_val)

        if committed_ratio >= 0.5:
            conf_score += 15
            conf_pos.append(f"{int(committed_ratio * 100)}% of open pipeline is classified as COMMITTED (+15)")
        elif committed_ratio >= 0.3:
            conf_score += 10
            conf_pos.append(f"{int(committed_ratio * 100)}% of open pipeline is COMMITTED (+10)")

        if at_risk_ratio >= 0.3:
            conf_score -= 20
            conf_neg.append(f"{int(at_risk_ratio * 100)}% of open pipeline value is AT RISK (-20)")
        elif at_risk_ratio >= 0.15:
            conf_score -= 10
            conf_neg.append(f"{int(at_risk_ratio * 100)}% of open pipeline value is AT RISK (-10)")
    else:
        conf_pos.append("No active open pipeline risks identified")

    # Concentration check
    deals_objs = [row[0] for row in deal_rows if row[0].status == "open"]
    conc_res = calculate_pipeline_concentration(deals_objs)
    if conc_res.is_concentrated:
        conf_score -= 15
        conf_neg.append(f"Pipeline concentration risk detected (top deals represent {conc_res.top_deals_value_ratio:.1f}% of open value) (-15)")
    else:
        conf_pos.append("Pipeline value is well diversified across accounts (+5)")
        conf_score += 5

    # Activity recency ratio
    if open_deal_items:
        recent_cnt = sum(1 for i in open_deal_items if i.health_status in ("healthy", "stable"))
        rec_ratio = recent_cnt / len(open_deal_items)
        if rec_ratio >= 0.7:
            conf_score += 10
            conf_pos.append(f"High activity coverage ({int(rec_ratio * 100)}% of open deals are active) (+10)")
        elif rec_ratio < 0.4:
            conf_score -= 10
            conf_neg.append(f"Low activity coverage ({int((1 - rec_ratio) * 100)}% of open deals lack recent touchpoints) (-10)")

    # Missing close dates check
    no_close_cnt = sum(1 for i in open_deal_items if i.expected_close_date is None)
    if open_deal_items and (no_close_cnt / len(open_deal_items)) > 0.2:
        conf_score -= 10
        conf_neg.append(f"{no_close_cnt} deal(s) lack expected close dates (-10)")

    conf_score = max(0, min(100, conf_score))

    if conf_score >= 80:
        conf_label = "HIGH CONFIDENCE"
    elif conf_score >= 60:
        conf_label = "MODERATE CONFIDENCE"
    elif conf_score >= 40:
        conf_label = "LOW CONFIDENCE"
    else:
        conf_label = "VERY LOW CONFIDENCE"

    # Apply query filtering to deal list if requested
    filtered_items = open_deal_items
    if stage:
        filtered_items = [i for i in filtered_items if i.stage == stage]
    if forecast_category:
        filtered_items = [i for i in filtered_items if i.forecast_category == forecast_category.upper()]
    if customer_id:
        filtered_items = [i for i in filtered_items if i.customer_id == customer_id]
    if period:
        if period == "current_month":
            filtered_items = [i for i in filtered_items if i.expected_close_date and i.expected_close_date.strftime("%Y-%m") == current_m]
        elif period == "next_month":
            filtered_items = [i for i in filtered_items if i.expected_close_date and i.expected_close_date.strftime("%Y-%m") == next_m]
        elif period == "no_close_date":
            filtered_items = [i for i in filtered_items if i.expected_close_date is None]

    return RevenueForecastResponse(
        open_pipeline=f"{open_pipeline_val:.2f}",
        weighted_pipeline=f"{weighted_pipeline_val:.2f}",
        forecast_revenue=f"{forecast_revenue_val:.2f}",
        committed_revenue=f"{committed_val:.2f}",
        upside_revenue=f"{upside_val:.2f}",
        at_risk_revenue=f"{at_risk_val:.2f}",
        won_revenue=f"{won_val:.2f}",
        lost_revenue=f"{lost_val:.2f}",
        confidence_score=conf_score,
        confidence_label=conf_label,
        concentration_risk=conc_res.is_concentrated,
        periods=periods_list,
        deals=filtered_items,
        confidence_factors=ForecastConfidenceFactors(
            positive_factors=conf_pos,
            negative_factors=conf_neg
        )
    )
