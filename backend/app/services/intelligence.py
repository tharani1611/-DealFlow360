import uuid
from datetime import datetime, timezone, timedelta, date
from decimal import Decimal
from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import status

from app.core.exceptions import NotFoundException
from app.models.customer import Customer
from app.models.deal import Deal
from app.models.quotation import Quotation
from app.models.activity import Activity
from app.models.contact import Contact
from app.schemas.intelligence import (
    RiskFactor,
    DealHealthMetrics,
    DealHealthResponse,
    CustomerEngagementMetrics,
    CustomerEngagementResponse,
    SalesBriefingResponse,
    StageDistributionItem,
    PipelineConcentration,
    PipelineMetrics,
    DashboardIntelligenceResponse,
    AttentionItem,
    AttentionCenterResponse,
    AlertNotification,
    AlertsResponse,
    ActivityProductivityMetrics
)


async def calculate_deal_health(
    db: AsyncSession,
    organization_id: uuid.UUID,
    deal_id: uuid.UUID
) -> DealHealthResponse:
    """Calculates deterministic deal health score (0-100), health classification, and risk factors."""
    deal_query = await db.execute(
        select(Deal).where(and_(Deal.id == deal_id, Deal.organization_id == organization_id))
    )
    deal = deal_query.scalar_one_or_none()
    if not deal:
        raise NotFoundException(f"Deal with ID {deal_id} was not found.")

    quotation = None
    if deal.quotation_id:
        q_query = await db.execute(
            select(Quotation).where(and_(Quotation.id == deal.quotation_id, Quotation.organization_id == organization_id))
        )
        quotation = q_query.scalar_one_or_none()

    act_query = await db.execute(
        select(Activity).where(and_(Activity.deal_id == deal_id, Activity.organization_id == organization_id))
    )
    activities = list(act_query.scalars().all())

    now_utc = datetime.now(timezone.utc)
    today_utc = now_utc.date()

    overdue_count = 0
    recent_activity_count = 0
    last_act_date: Optional[datetime] = None

    for act in activities:
        if act.status not in ("completed", "cancelled") and act.due_at:
            due_dt = act.due_at if isinstance(act.due_at, datetime) else datetime.combine(act.due_at, datetime.min.time(), tzinfo=timezone.utc)
            if due_dt.tzinfo is None:
                due_dt = due_dt.replace(tzinfo=timezone.utc)
            if due_dt < now_utc:
                overdue_count += 1

        act_time = act.created_at or act.updated_at
        if act_time:
            if act_time.tzinfo is None:
                act_time = act_time.replace(tzinfo=timezone.utc)
            if (now_utc - act_time).days <= 7:
                recent_activity_count += 1
            if last_act_date is None or act_time > last_act_date:
                last_act_date = act_time

    days_since_last_act = (now_utc - last_act_date).days if last_act_date else 999

    days_until_close: Optional[int] = None
    if deal.expected_close_date:
        close_d = deal.expected_close_date if isinstance(deal.expected_close_date, date) else deal.expected_close_date.date()
        days_until_close = (close_d - today_utc).days

    has_accepted = quotation.status == "accepted" if quotation else False
    has_expired_or_rejected = quotation.status in ("rejected", "expired") if quotation else False

    metrics = DealHealthMetrics(
        probability=deal.probability,
        overdue_activity_count=overdue_count,
        days_until_expected_close=days_until_close,
        recent_activity_count=recent_activity_count,
        has_accepted_quotation=has_accepted,
        has_expired_or_rejected_quotation=has_expired_or_rejected
    )

    score = 0
    if deal.status == "won":
        score = 100
    elif deal.status == "lost":
        score = 0
    else:
        stage_baseline = {
            "new": 40,
            "qualified": 55,
            "proposal": 70,
            "negotiation": 85
        }
        score = stage_baseline.get(deal.stage, 50)
        score += int(deal.probability * 0.3)

        if days_since_last_act <= 7:
            score += 15
        elif days_since_last_act <= 14:
            score += 5
        elif days_since_last_act > 30:
            score -= 20
        else:
            score -= 5

        score -= min(30, overdue_count * 15)

        if days_until_close is not None and days_until_close <= 7:
            if deal.stage in ("new", "qualified") or days_since_last_act > 7:
                score -= 20

        if quotation:
            if quotation.status == "accepted":
                score += 15
            elif quotation.status == "sent":
                score += 5
            elif quotation.status == "rejected":
                score -= 25
            elif quotation.status == "expired":
                score -= 15

    score = max(0, min(100, score))

    if score >= 80:
        health_status = "healthy"
    elif score >= 60:
        health_status = "stable"
    elif score >= 40:
        health_status = "at_risk"
    else:
        health_status = "critical"

    risk_factors: List[RiskFactor] = []

    if overdue_count > 0:
        risk_factors.append(RiskFactor(
            code="OVERDUE_ACTIVITY",
            severity="high" if overdue_count >= 2 else "medium",
            title="Overdue CRM Activities",
            description=f"{overdue_count} scheduled action item(s) are overdue.",
            recommendation="Complete or reschedule overdue follow-up tasks immediately."
        ))

    if days_since_last_act > 14 and deal.status == "open":
        risk_factors.append(RiskFactor(
            code="NO_RECENT_ACTIVITY",
            severity="medium" if days_since_last_act <= 30 else "high",
            title="Inactive Engagement",
            description=f"No activity recorded in the last {days_since_last_act} days.",
            recommendation="Reach out to primary contact to re-engage interest."
        ))

    if days_until_close is not None and days_until_close <= 7 and deal.stage in ("new", "qualified") and deal.status == "open":
        risk_factors.append(RiskFactor(
            code="CLOSING_SOON_LOW_STAGE",
            severity="high",
            title="Imminent Close Date in Early Stage",
            description=f"Expected close date is in {days_until_close} days but deal is still in '{deal.stage}' stage.",
            recommendation="Update close date or advance stage to proposal/negotiation."
        ))

    if deal.value >= Decimal("50000.00") and deal.probability < 30 and deal.status == "open":
        risk_factors.append(RiskFactor(
            code="LOW_PROBABILITY_HIGH_VALUE",
            severity="high",
            title="High Value / Low Win Probability",
            description=f"Deal value is ${deal.value:,.2f} with low win probability ({deal.probability}%).",
            recommendation="Focus on key decision criteria to boost win confidence."
        ))

    if quotation and quotation.status == "rejected" and deal.status == "open":
        risk_factors.append(RiskFactor(
            code="QUOTATION_REJECTED",
            severity="critical",
            title="Quotation Rejected",
            description="The latest quotation was rejected by the customer.",
            recommendation="Review price structure or terms and issue a revised quote."
        ))

    if quotation and quotation.status == "expired" and deal.status == "open":
        risk_factors.append(RiskFactor(
            code="QUOTATION_EXPIRED",
            severity="medium",
            title="Quotation Expired",
            description="The quotation validity period has elapsed.",
            recommendation="Extend validity date or reissue quote."
        ))

    created_dt = deal.created_at
    if created_dt:
        if created_dt.tzinfo is None:
            created_dt = created_dt.replace(tzinfo=timezone.utc)
        if (now_utc - created_dt).days > 30 and deal.stage == "new" and deal.status == "open":
            risk_factors.append(RiskFactor(
                code="STALLED_DEAL",
                severity="medium",
                title="Stalled New Opportunity",
                description="Deal has remained in 'new' stage for over 30 days.",
                recommendation="Qualify customer requirement or archive deal."
            ))

    has_critical_factor = any(rf.severity == "critical" for rf in risk_factors)
    has_high_factor = any(rf.severity == "high" for rf in risk_factors)

    if has_critical_factor or health_status == "critical":
        risk_level = "critical"
    elif has_high_factor or health_status == "at_risk":
        risk_level = "high"
    elif len(risk_factors) > 0 or health_status == "stable":
        risk_level = "medium"
    else:
        risk_level = "low"

    return DealHealthResponse(
        deal_id=deal.id,
        deal_number=deal.deal_number,
        title=deal.title,
        health_score=score,
        health_status=health_status,
        risk_level=risk_level,
        risk_factors=risk_factors,
        metrics=metrics,
        ai_explanation=None
    )


async def calculate_customer_engagement(
    db: AsyncSession,
    organization_id: uuid.UUID,
    customer_id: uuid.UUID
) -> CustomerEngagementResponse:
    """Calculates deterministic customer engagement score (0-100) and cooling detection."""
    cust_query = await db.execute(
        select(Customer).where(and_(Customer.id == customer_id, Customer.organization_id == organization_id))
    )
    customer = cust_query.scalar_one_or_none()
    if not customer:
        raise NotFoundException(f"Customer with ID {customer_id} was not found.")

    now_utc = datetime.now(timezone.utc)

    act_query = await db.execute(
        select(Activity).where(and_(Activity.customer_id == customer_id, Activity.organization_id == organization_id))
    )
    activities = list(act_query.scalars().all())

    deal_query = await db.execute(
        select(Deal).where(and_(Deal.customer_id == customer_id, Deal.organization_id == organization_id, Deal.status == "open"))
    )
    open_deals = list(deal_query.scalars().all())

    quote_query = await db.execute(
        select(Quotation).where(and_(Quotation.customer_id == customer_id, Quotation.organization_id == organization_id, Quotation.status == "accepted"))
    )
    accepted_quotes = list(quote_query.scalars().all())

    recent_30d_count = 0
    overdue_count = 0
    last_act_at: Optional[datetime] = None

    for act in activities:
        act_time = act.created_at or act.updated_at
        if act_time:
            if act_time.tzinfo is None:
                act_time = act_time.replace(tzinfo=timezone.utc)
            if (now_utc - act_time).days <= 30:
                recent_30d_count += 1
            if last_act_at is None or act_time > last_act_at:
                last_act_at = act_time

        if act.status not in ("completed", "cancelled") and act.due_at:
            due_dt = act.due_at if isinstance(act.due_at, datetime) else datetime.combine(act.due_at, datetime.min.time(), tzinfo=timezone.utc)
            if due_dt.tzinfo is None:
                due_dt = due_dt.replace(tzinfo=timezone.utc)
            if due_dt < now_utc:
                overdue_count += 1

    days_since_last_act = (now_utc - last_act_at).days if last_act_at else 999
    total_deal_val = sum((d.value for d in open_deals), Decimal("0.00"))

    metrics = CustomerEngagementMetrics(
        last_activity_at=last_act_at,
        recent_activity_count_30d=recent_30d_count,
        overdue_activity_count=overdue_count,
        open_deal_count=len(open_deals),
        total_open_deal_value=f"{total_deal_val:.2f}",
        accepted_quotation_count=len(accepted_quotes)
    )

    score = 0
    if days_since_last_act <= 7:
        score += 30
    elif days_since_last_act <= 14:
        score += 20
    elif days_since_last_act <= 30:
        score += 10

    score += min(30, recent_30d_count * 10)
    score += min(20, len(open_deals) * 10)
    score += min(20, len(accepted_quotes) * 10)
    score -= (overdue_count * 10)

    score = max(0, min(100, score))

    if score >= 80:
        status_label = "highly_engaged"
    elif score >= 60:
        status_label = "engaged"
    elif score >= 40:
        status_label = "cooling"
    else:
        status_label = "cold"

    is_cold = status_label in ("cooling", "cold")

    risk_reasons: List[str] = []
    if days_since_last_act > 30:
        risk_reasons.append("No recorded interactions in over 30 days.")
    elif days_since_last_act > 14:
        risk_reasons.append("Interaction frequency has slowed down over the last 2 weeks.")

    if overdue_count > 0:
        risk_reasons.append(f"{overdue_count} follow-up task(s) are overdue.")

    if len(open_deals) > 0 and recent_30d_count == 0:
        risk_reasons.append("Active pipeline exists without recent customer interactions.")

    return CustomerEngagementResponse(
        customer_id=customer.id,
        customer_name=customer.name,
        engagement_score=score,
        engagement_status=status_label,
        is_going_cold=is_cold,
        metrics=metrics,
        risk_reasons=risk_reasons,
        ai_explanation=None
    )


def calculate_pipeline_concentration(open_deals: List[Deal]) -> PipelineConcentration:
    """Evaluates pipeline concentration risk where top 2 deals account for > 50% of open value."""
    if not open_deals or len(open_deals) == 0:
        return PipelineConcentration(top_deals_value_ratio=0.0, is_concentrated=False)

    sorted_deals = sorted(open_deals, key=lambda d: d.value, reverse=True)
    total_val = sum((d.value for d in open_deals), Decimal("0.00"))

    if total_val == Decimal("0.00"):
        return PipelineConcentration(top_deals_value_ratio=0.0, is_concentrated=False)

    top_2_val = sum((d.value for d in sorted_deals[:2]), Decimal("0.00"))
    ratio = float((top_2_val / total_val) * 100)
    is_conc = ratio >= 50.0

    rec = "Prioritize deal diversification and smaller account follow-ups." if is_conc else "Pipeline value distribution is well balanced across accounts."

    return PipelineConcentration(
        top_deals_value_ratio=round(ratio, 1),
        is_concentrated=is_conc,
        top_deals_count=min(2, len(open_deals)),
        recommendation=rec
    )


async def calculate_pipeline_intelligence(
    db: AsyncSession,
    organization_id: uuid.UUID
) -> DashboardIntelligenceResponse:
    """Calculates deterministic executive pipeline financial metrics, concentration, and intelligence widgets."""
    deals_query = await db.execute(
        select(Deal).where(Deal.organization_id == organization_id)
    )
    all_deals = list(deals_query.scalars().all())

    open_deals = [d for d in all_deals if d.status == "open"]
    won_deals = [d for d in all_deals if d.status == "won"]
    lost_deals = [d for d in all_deals if d.status == "lost"]

    open_val = sum((d.value for d in open_deals), Decimal("0.00"))
    weighted_val = sum((d.value * Decimal(d.probability) / Decimal(100) for d in open_deals), Decimal("0.00"))
    won_val = sum((d.value for d in won_deals), Decimal("0.00"))
    lost_val = sum((d.value for d in lost_deals), Decimal("0.00"))
    at_risk_val = Decimal("0.00")

    health_counts = {"healthy": 0, "stable": 0, "at_risk": 0, "critical": 0}
    deals_at_risk: List[DealHealthResponse] = []
    needs_attention_count = 0

    for deal in open_deals:
        health_resp = await calculate_deal_health(db, organization_id, deal.id)
        health_counts[health_resp.health_status] += 1

        if health_resp.health_status in ("at_risk", "critical"):
            at_risk_val += deal.value
            deals_at_risk.append(health_resp)
            needs_attention_count += 1
        elif len(health_resp.risk_factors) > 0:
            needs_attention_count += 1

    for deal in won_deals:
        health_counts["healthy"] += 1
    for deal in lost_deals:
        health_counts["critical"] += 1

    # Stage breakdown
    stage_names = ["new", "qualified", "proposal", "negotiation"]
    stage_items: List[StageDistributionItem] = []
    for stg in stage_names:
        stg_deals = [d for d in open_deals if d.stage == stg]
        stg_tot = sum((d.value for d in stg_deals), Decimal("0.00"))
        stg_wt = sum((d.value * Decimal(d.probability) / Decimal(100) for d in stg_deals), Decimal("0.00"))
        stage_items.append(StageDistributionItem(
            stage=stg,
            count=len(stg_deals),
            total_value=f"{stg_tot:.2f}",
            weighted_value=f"{stg_wt:.2f}"
        ))

    # Concentration
    conc = calculate_pipeline_concentration(open_deals)

    # Win rate (closed deals: won / (won + lost))
    closed_cnt = len(won_deals) + len(lost_deals)
    win_rate_str = f"{int((len(won_deals) / closed_cnt) * 100)}%" if closed_cnt > 0 else "0%"

    avg_val = (open_val / Decimal(len(open_deals))) if len(open_deals) > 0 else Decimal("0.00")

    # Fetch cooling customers
    cust_query = await db.execute(
        select(Customer).where(and_(Customer.organization_id == organization_id, Customer.is_active == True))
    )
    customers = list(cust_query.scalars().all())

    cooling_customers: List[CustomerEngagementResponse] = []
    for cust in customers:
        eng_resp = await calculate_customer_engagement(db, organization_id, cust.id)
        if eng_resp.is_going_cold:
            cooling_customers.append(eng_resp)
            needs_attention_count += 1

    pipeline = PipelineMetrics(
        open_pipeline_value=f"{open_val:.2f}",
        weighted_pipeline_value=f"{weighted_val:.2f}",
        won_pipeline_value=f"{won_val:.2f}",
        lost_pipeline_value=f"{lost_val:.2f}",
        at_risk_pipeline_value=f"{at_risk_val:.2f}",
        win_rate=win_rate_str,
        average_deal_value=f"{avg_val:.2f}",
        forecast_confidence_label="CRM-derived weighted probability estimate",
        concentration=conc,
        stage_breakdown=stage_items
    )

    return DashboardIntelligenceResponse(
        pipeline=pipeline,
        deal_health_counts=health_counts,
        deals_at_risk=deals_at_risk[:5],
        customers_going_cold=cooling_customers[:5],
        needs_attention_count=needs_attention_count
    )


# Phase 15 Service Methods
async def get_sales_attention_items(
    db: AsyncSession,
    organization_id: uuid.UUID
) -> AttentionCenterResponse:
    """Generates prioritized Sales Attention Center items."""
    now_utc = datetime.now(timezone.utc)
    today_utc = now_utc.date()

    items: List[AttentionItem] = []

    # 1. Overdue activities
    act_query = await db.execute(
        select(Activity).where(and_(Activity.organization_id == organization_id, Activity.status == "pending"))
    )
    pending_activities = list(act_query.scalars().all())

    for act in pending_activities:
        if act.due_at:
            due_dt = act.due_at if isinstance(act.due_at, datetime) else datetime.combine(act.due_at, datetime.min.time(), tzinfo=timezone.utc)
            if due_dt.tzinfo is None:
                due_dt = due_dt.replace(tzinfo=timezone.utc)
            if due_dt < now_utc:
                days_overdue = (now_utc - due_dt).days
                items.append(AttentionItem(
                    id=f"act-overdue-{act.id}",
                    type="activity_overdue",
                    priority="critical" if days_overdue >= 3 else "high",
                    title=act.title,
                    description=f"Activity is {days_overdue} day(s) overdue.",
                    entity_type="activity",
                    entity_id=act.id,
                    action_label="Open Activity"
                ))

    # 2. Deals at risk & closing soon
    deal_query = await db.execute(
        select(Deal).where(and_(Deal.organization_id == organization_id, Deal.status == "open"))
    )
    open_deals = list(deal_query.scalars().all())

    for deal in open_deals:
        dh = await calculate_deal_health(db, organization_id, deal.id)
        if dh.health_status in ("critical", "at_risk"):
            items.append(AttentionItem(
                id=f"deal-risk-{deal.id}",
                type="deal_risk",
                priority="critical" if dh.health_status == "critical" else "high",
                title=f"Deal at Risk: {deal.title}",
                description=f"Health score is {dh.health_score}/100 with {len(dh.risk_factors)} risk factors.",
                entity_type="deal",
                entity_id=deal.id,
                action_label="View Deal"
            ))

        if deal.expected_close_date:
            close_d = deal.expected_close_date if isinstance(deal.expected_close_date, date) else deal.expected_close_date.date()
            days_to_close = (close_d - today_utc).days
            if 0 <= days_to_close <= 7 and deal.stage in ("new", "qualified"):
                items.append(AttentionItem(
                    id=f"deal-close-{deal.id}",
                    type="deal_closing",
                    priority="high",
                    title=f"Deal Closing Soon: {deal.title}",
                    description=f"Closing in {days_to_close} day(s) but currently in '{deal.stage}' stage.",
                    entity_type="deal",
                    entity_id=deal.id,
                    action_label="View Deal"
                ))

    # 3. Cooling customers
    cust_query = await db.execute(
        select(Customer).where(and_(Customer.organization_id == organization_id, Customer.is_active == True))
    )
    customers = list(cust_query.scalars().all())

    for cust in customers:
        eng = await calculate_customer_engagement(db, organization_id, cust.id)
        if eng.is_going_cold:
            items.append(AttentionItem(
                id=f"cust-cold-{cust.id}",
                type="customer_cooling",
                priority="medium",
                title=f"Account Cooling: {cust.name}",
                description=f"Engagement score dropped to {eng.engagement_score}/100.",
                entity_type="customer",
                entity_id=cust.id,
                action_label="View Customer"
            ))

    # Sort items by priority
    priority_map = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    items.sort(key=lambda x: priority_map.get(x.priority, 4))

    crit_cnt = sum(1 for i in items if i.priority == "critical")
    high_cnt = sum(1 for i in items if i.priority == "high")

    return AttentionCenterResponse(
        items=items,
        critical_count=crit_cnt,
        high_count=high_cnt,
        total_count=len(items)
    )


async def get_activity_productivity_metrics(
    db: AsyncSession,
    organization_id: uuid.UUID
) -> ActivityProductivityMetrics:
    """Computes productivity metrics for activity filtering."""
    now_utc = datetime.now(timezone.utc)
    today_utc = now_utc.date()
    week_ago = now_utc - timedelta(days=7)

    act_query = await db.execute(
        select(Activity).where(Activity.organization_id == organization_id)
    )
    all_activities = list(act_query.scalars().all())

    today_cnt = 0
    upcoming_cnt = 0
    overdue_cnt = 0
    completed_week_cnt = 0

    for act in all_activities:
        if act.status == "pending" and act.due_at:
            due_d = act.due_at if isinstance(act.due_at, date) else act.due_at.date()
            due_dt = act.due_at if isinstance(act.due_at, datetime) else datetime.combine(act.due_at, datetime.min.time(), tzinfo=timezone.utc)
            if due_dt.tzinfo is None:
                due_dt = due_dt.replace(tzinfo=timezone.utc)

            if due_d == today_utc:
                today_cnt += 1
            if 0 <= (due_d - today_utc).days <= 7:
                upcoming_cnt += 1
            if due_dt < now_utc:
                overdue_cnt += 1

        if act.status == "completed" and act.updated_at:
            upd_dt = act.updated_at
            if upd_dt.tzinfo is None:
                upd_dt = upd_dt.replace(tzinfo=timezone.utc)
            if upd_dt >= week_ago:
                completed_week_cnt += 1

    return ActivityProductivityMetrics(
        today_count=today_cnt,
        upcoming_7d_count=upcoming_cnt,
        overdue_count=overdue_cnt,
        completed_this_week_count=completed_week_cnt
    )


async def generate_derived_alerts(
    db: AsyncSession,
    organization_id: uuid.UUID
) -> AlertsResponse:
    """Generates derived in-app notification alerts feed for topbar header."""
    att = await get_sales_attention_items(db, organization_id)

    alerts: List[AlertNotification] = []
    for item in att.items:
        severity = "critical" if item.priority == "critical" else "warning" if item.priority == "high" else "info"
        alerts.append(AlertNotification(
            id=item.id,
            type=item.type,
            severity=severity,
            title=item.title,
            message=item.description,
            entity_type=item.entity_type,
            entity_id=item.entity_id
        ))

    return AlertsResponse(
        alerts=alerts,
        unread_count=len(alerts),
        generated_at=datetime.now(timezone.utc)
    )
