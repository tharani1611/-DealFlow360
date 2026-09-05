import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.customer import Customer
from app.models.contact import Contact
from app.models.deal import Deal
from app.models.quotation import Quotation
from app.models.activity import Activity
from app.core.exceptions import NotFoundException
from app.schemas.intelligence import (
    DealHealthResponse,
    CustomerEngagementResponse,
    SalesBriefingResponse,
    DashboardIntelligenceResponse,
    AttentionCenterResponse,
    AlertsResponse,
    ActivityProductivityMetrics,
    Customer360IntelligenceResponse,
    Product360IntelligenceResponse,
    ProductAffinityItem
)
from app.schemas.health_monitoring import (
    DealHealthEvaluationResponse,
    StalledQuotesResponse,
    DiscountAnomaliesResponse,
    DeliverySlippageResponse,
    NudgeResponse,
    NudgeActionRequest,
    ExecutiveReportingSummary,
)
from app.schemas.product_recommendation import CustomerProductRecommendationsResponse
from app.schemas.forecast import RevenueForecastResponse, ForecastExplanationResponse
from app.services import product_recommendations as recommendation_service
from app.services.customer_intelligence import customer_intelligence_service
from app.services.product_intelligence import product_intelligence_service
from app.services import intelligence as intelligence_service
from app.services import forecast as forecast_service
from app.services.deal_health_engine import deal_health_engine
from app.services.stalled_quote_engine import stalled_quote_engine
from app.services.discount_anomaly_engine import discount_anomaly_engine
from app.services.delivery_slippage_engine import delivery_slippage_engine
from app.services.nudge_engine import nudge_engine
from app.services.reporting_engine import reporting_engine
from app.services.analytics_service import analytics_service
from app.ai.service import ai_service
from datetime import date

router = APIRouter()


@router.get(
    "/forecast",
    response_model=RevenueForecastResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Executive Revenue Forecast & Prediction Intelligence",
    description="Calculates deterministic revenue forecast, confidence score (0-100), deal classifications, and period breakdowns."
)
async def get_revenue_forecast(
    period: Optional[str] = None,
    stage: Optional[str] = None,
    forecast_category: Optional[str] = None,
    customer_id: Optional[uuid.UUID] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> RevenueForecastResponse:
    """Retrieves executive revenue forecast intelligence."""
    return await forecast_service.calculate_revenue_forecast(
        db,
        current_user.organization_id,
        period=period,
        stage=stage,
        forecast_category=forecast_category,
        customer_id=customer_id
    )


@router.get(
    "/forecast/explain",
    response_model=ForecastExplanationResponse,
    status_code=status.HTTP_200_OK,
    summary="Get AI Executive Revenue Forecast Explanation",
    description="Generates AI executive commentary and risk advisory based on deterministic forecast facts."
)
async def explain_revenue_forecast(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> ForecastExplanationResponse:
    """Generates AI executive commentary for revenue forecast."""
    forecast = await forecast_service.calculate_revenue_forecast(db, current_user.organization_id)
    summary_text = await ai_service.explain_revenue_forecast(db, current_user.organization_id, forecast)
    
    return ForecastExplanationResponse(
        summary=summary_text,
        risk_highlights=forecast.confidence_factors.negative_factors,
        recommendations=[
            "Focus sales reps on deals marked as AT_RISK with overdue activity items.",
            "Verify close dates for deals currently missing scheduled target dates.",
            "Accelerate final negotiation steps for high-probability COMMITTED opportunities."
        ]
    )


@router.get(
    "/customers/{customer_id}/product-recommendations",
    response_model=CustomerProductRecommendationsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Customer Upsell & Cross-sell Product Recommendations",
    description="Evaluates deterministic product recommendation rules (upsell & cross-sell) for a customer."
)
async def get_customer_product_recommendations(
    customer_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> CustomerProductRecommendationsResponse:
    """Retrieves customer upsell and cross-sell product recommendations."""
    return await recommendation_service.get_customer_product_recommendations(
        db, current_user.organization_id, customer_id
    )


@router.get(
    "/deals/{deal_id}/health",
    response_model=DealHealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Deal Health & Risk Telemetry",
    description="Calculates deterministic deal health score (0-100), risk factors, and AI explanation."
)
async def get_deal_health(
    deal_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> DealHealthResponse:
    """Retrieves deterministic deal health and risk classification."""
    health_resp = await intelligence_service.calculate_deal_health(db, current_user.organization_id, deal_id)
    explanation = await ai_service.explain_deal_health(db, current_user.organization_id, deal_id, health_resp)
    health_resp.ai_explanation = explanation
    return health_resp


@router.get(
    "/customers/{customer_id}/engagement",
    response_model=CustomerEngagementResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Customer Engagement Score & Cooling Detection",
    description="Calculates customer engagement score (0-100), cooling detection, and interaction telemetry."
)
async def get_customer_engagement(
    customer_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> CustomerEngagementResponse:
    """Retrieves customer relationship engagement telemetry."""
    return await intelligence_service.calculate_customer_engagement(db, current_user.organization_id, customer_id)


@router.get(
    "/customers/{customer_id}/briefing",
    response_model=SalesBriefingResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Executive Sales & Account Briefing",
    description="Generates executive account snapshot, talking points, next best actions, and follow-up draft."
)
async def get_sales_briefing(
    customer_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> SalesBriefingResponse:
    """Retrieves synthesized Sales Briefing for customer meeting preparation."""
    org_id = current_user.organization_id

    cust_q = await db.execute(
        select(Customer).where(and_(Customer.id == customer_id, Customer.organization_id == org_id))
    )
    customer = cust_q.scalar_one_or_none()
    if not customer:
        raise NotFoundException(f"Customer with ID {customer_id} was not found.")

    contact_q = await db.execute(
        select(Contact).where(and_(Contact.customer_id == customer_id, Contact.organization_id == org_id, Contact.is_primary == True))
    )
    primary_contact = contact_q.scalar_one_or_none()
    if not primary_contact:
        c_q = await db.execute(
            select(Contact).where(and_(Contact.customer_id == customer_id, Contact.organization_id == org_id))
        )
        primary_contact = c_q.scalars().first()

    contact_name = f"{primary_contact.first_name} {primary_contact.last_name}" if primary_contact else None
    contact_email = primary_contact.email if primary_contact else None

    eng = await intelligence_service.calculate_customer_engagement(db, org_id, customer_id)

    deals_q = await db.execute(
        select(Deal).where(and_(Deal.customer_id == customer_id, Deal.organization_id == org_id, Deal.status == "open"))
    )
    open_deals = list(deals_q.scalars().all())

    deal_summaries = []
    for d in open_deals:
        dh = await intelligence_service.calculate_deal_health(db, org_id, d.id)
        deal_summaries.append({
            "deal_id": str(d.id),
            "deal_number": d.deal_number,
            "title": d.title,
            "stage": d.stage,
            "value": str(d.value),
            "health_score": dh.health_score,
            "health_status": dh.health_status
        })

    act_q = await db.execute(
        select(Activity).where(and_(Activity.customer_id == customer_id, Activity.organization_id == org_id))
    )
    acts = list(act_q.scalars().all())
    overdue_cnt = sum(1 for a in acts if a.status not in ("completed", "cancelled") and a.due_date)

    attention_items = list(eng.risk_reasons)
    if overdue_cnt > 0:
        attention_items.append(f"{overdue_cnt} activity item(s) are overdue for this account.")

    briefing = SalesBriefingResponse(
        customer_id=customer.id,
        customer_name=customer.name,
        primary_contact_name=contact_name,
        primary_contact_email=contact_email,
        relationship_status=eng.engagement_status.upper().replace("_", " "),
        engagement_score=eng.engagement_score,
        open_pipeline_value=eng.metrics.total_open_deal_value,
        active_deals_count=len(open_deals),
        overdue_activities_count=overdue_cnt,
        deal_health_summary=deal_summaries,
        attention_items=attention_items,
        talking_points=[
            f"Discuss active pipeline opportunity with total value of ${eng.metrics.total_open_deal_value}.",
            "Review customer feedback on active quotations and proposal terms.",
            "Confirm timeline for upcoming milestone decision."
        ],
        suggested_next_actions=[
            {
                "title": f"Schedule follow-up call with {contact_name or customer.name}",
                "action_type": "call",
                "priority": "high"
            }
        ],
        suggested_followup_message=f"Hi {contact_name or customer.name},\n\nFollowing up on our recent commercial discussions regarding {customer.name}. We'd love to connect to review next steps and answer any questions.\n\nBest regards,\nSales Team"
    )

    return await ai_service.generate_sales_briefing(db, org_id, customer_id, briefing)


@router.get(
    "/dashboard",
    response_model=DashboardIntelligenceResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Dashboard CRM Intelligence",
    description="Retrieves aggregate pipeline financial metrics, deals at risk, and cooling customers."
)
async def get_dashboard_intelligence(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> DashboardIntelligenceResponse:
    """Retrieves executive CRM pipeline intelligence and attention items."""
    return await intelligence_service.calculate_pipeline_intelligence(db, current_user.organization_id)


# Phase 15 Endpoints
@router.get(
    "/attention",
    response_model=AttentionCenterResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Sales Attention Center Items",
    description="Retrieves prioritized actionable attention items (overdue tasks, risky deals, cooling accounts)."
)
async def get_sales_attention(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> AttentionCenterResponse:
    """Retrieves prioritized sales attention items."""
    return await intelligence_service.get_sales_attention_items(db, current_user.organization_id)


@router.get(
    "/alerts",
    response_model=AlertsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get In-App Alert Notifications Feed",
    description="Retrieves derived alert notifications feed for the application topbar notification drawer."
)
async def get_derived_alerts(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> AlertsResponse:
    """Retrieves derived in-app alert notification feed."""
    return await intelligence_service.generate_derived_alerts(db, current_user.organization_id)


@router.get(
    "/activity-productivity",
    response_model=ActivityProductivityMetrics,
    status_code=status.HTTP_200_OK,
    summary="Get Activity Productivity Metrics",
    description="Retrieves counts for today, upcoming 7d, overdue, and completed this week activities."
)
async def get_activity_productivity(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> ActivityProductivityMetrics:
    """Retrieves activity productivity metrics."""
    return await intelligence_service.get_activity_productivity_metrics(db, current_user.organization_id)


# Phase 41-45 Endpoints: Customer 360 & Product 360 Intelligence

@router.get(
    "/customers/{customer_id}/360",
    response_model=Customer360IntelligenceResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Customer 360 Intelligence",
    description="Calculates comprehensive Customer 360 intelligence, health score, positive/negative drivers, segmentation, and trends."
)
async def get_customer_360_intelligence(
    customer_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Customer360IntelligenceResponse:
    """Retrieves Customer 360 Intelligence payload with health score, drivers, and trends."""
    cust_360 = await customer_intelligence_service.get_customer_360_intelligence(
        db, current_user.organization_id, customer_id
    )
    explanation = await ai_service.explain_customer_health(
        db, current_user.organization_id, cust_360
    )
    cust_360.ai_explanation = explanation
    return cust_360


@router.get(
    "/products/{product_id}/360",
    response_model=Product360IntelligenceResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Product 360 Intelligence",
    description="Calculates Product 360 performance, gross margin, penetration rate, popularity rank, and co-purchase affinities."
)
async def get_product_360_intelligence(
    product_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Product360IntelligenceResponse:
    """Retrieves Product 360 Intelligence payload with performance KPIs, affinities, and AI advisory."""
    prod_360 = await product_intelligence_service.get_product_360_intelligence(
        db, current_user.organization_id, product_id
    )
    explanation = await ai_service.explain_product_performance(
        db, current_user.organization_id, prod_360
    )
    prod_360.ai_explanation = explanation
    return prod_360


# Phase 53–59 Endpoints: Health, Monitoring, Nudges, Reporting & Analytics

@router.get(
    "/deals/{deal_id}/health-evaluation",
    response_model=DealHealthEvaluationResponse,
    status_code=status.HTTP_200_OK,
    summary="Phase 53: Authoritative Deal Health Evaluation",
    description="Evaluates multi-dimensional deal telemetry, status classification, positive/negative drivers, and persists snapshot."
)
async def evaluate_deal_health(
    deal_id: uuid.UUID,
    persist_snapshot: bool = True,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> DealHealthEvaluationResponse:
    return await deal_health_engine.evaluate_deal_health(
        db, current_user.organization_id, deal_id, persist_snapshot=persist_snapshot
    )


@router.get(
    "/quotations/stalled",
    response_model=StalledQuotesResponse,
    status_code=status.HTTP_200_OK,
    summary="Phase 54: Stalled Quotation Detection",
    description="Detects quotations inactive past thresholds while excluding false positives."
)
async def get_stalled_quotations(
    days_threshold: int = 14,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> StalledQuotesResponse:
    return await stalled_quote_engine.detect_stalled_quotes(
        db, current_user.organization_id, days_threshold=days_threshold
    )


@router.get(
    "/discounts/anomalies",
    response_model=DiscountAnomaliesResponse,
    status_code=status.HTTP_200_OK,
    summary="Phase 55: Discount Anomaly Monitoring",
    description="Monitors unusual commercial discount behavior compared against customer and org baselines."
)
async def get_discount_anomalies(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> DiscountAnomaliesResponse:
    return await discount_anomaly_engine.monitor_discount_anomalies(
        db, current_user.organization_id
    )


@router.get(
    "/deliveries/slippage",
    response_model=DeliverySlippageResponse,
    status_code=status.HTTP_200_OK,
    summary="Phase 56: Delivery Slippage Monitoring",
    description="Monitors delivery promises, slippage days, status classification, and root causes."
)
async def get_delivery_slippage(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> DeliverySlippageResponse:
    return await delivery_slippage_engine.monitor_delivery_slippage(
        db, current_user.organization_id
    )


@router.get(
    "/nudges",
    response_model=List[NudgeResponse],
    status_code=status.HTTP_200_OK,
    summary="Phase 57: List Actionable Nudges",
    description="Retrieves active and historical system nudges."
)
async def list_nudges(
    status: Optional[str] = None,
    severity: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> List[NudgeResponse]:
    return await nudge_engine.list_nudges(
        db, current_user.organization_id, status=status, severity=severity
    )


@router.post(
    "/nudges/generate",
    response_model=List[NudgeResponse],
    status_code=status.HTTP_200_OK,
    summary="Phase 57: Evaluate and Generate System Nudges",
    description="Evaluates monitoring telemetry and idempotently generates new system nudges."
)
async def generate_system_nudges(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> List[NudgeResponse]:
    return await nudge_engine.evaluate_and_generate_system_nudges(
        db, current_user.organization_id
    )


@router.post(
    "/nudges/{nudge_id}/status",
    response_model=NudgeResponse,
    status_code=status.HTTP_200_OK,
    summary="Phase 57: Update Nudge Lifecycle Status",
    description="Transitions nudge status (ACKNOWLEDGED, COMPLETED, DISMISSED, ESCALATED) and logs audit entry."
)
async def update_nudge_status(
    nudge_id: uuid.UUID,
    target_status: str,
    payload: Optional[NudgeActionRequest] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> NudgeResponse:
    notes = payload.notes if payload else None
    return await nudge_engine.transition_nudge_status(
        db, current_user.organization_id, nudge_id, target_status=target_status, actor_id=current_user.id, notes=notes
    )


@router.get(
    "/reports/summary",
    response_model=ExecutiveReportingSummary,
    status_code=status.HTTP_200_OK,
    summary="Phase 58: Authoritative Executive Reporting Summary",
    description="Aggregates metrics across 6 core domains with Decimal financial accuracy."
)
async def get_executive_report_summary(
    period: str = "this_month",
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> ExecutiveReportingSummary:
    return await reporting_engine.generate_executive_report(
        db, current_user.organization_id, period=period, start_date=start_date, end_date=end_date
    )


@router.get(
    "/analytics/dashboard",
    status_code=status.HTTP_200_OK,
    summary="Phase 59: Executive Dashboard Analytics API",
    description="Consolidates reporting, monitoring, and nudge telemetry into an executive dashboard payload."
)
async def get_executive_dashboard_analytics(
    period: str = "this_month",
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return await analytics_service.get_dashboard_executive_analytics(
        db, current_user.organization_id, period=period
    )


