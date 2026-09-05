from uuid import UUID
from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict, Field


# Phase 53: Deal Health Engine
class DealHealthEvaluationResponse(BaseModel):
    deal_id: UUID
    deal_number: str
    title: str
    health_score: int = Field(..., ge=0, le=100)
    health_status: str  # HEALTHY, ATTENTION, AT_RISK, CRITICAL, UNKNOWN
    positive_drivers: List[str] = []
    negative_drivers: List[str] = []
    metrics_snapshot: Dict[str, Any] = {}
    calculated_at: datetime
    calculation_version: str = "1.0"
    ai_explanation: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


class DealHealthSnapshotResponse(BaseModel):
    id: UUID
    organization_id: UUID
    deal_id: UUID
    score: int
    status: str
    positive_drivers: List[str]
    negative_drivers: List[str]
    calculated_at: datetime
    calculation_version: str
    model_config = ConfigDict(from_attributes=True)


# Phase 54: Stalled Quote Detection
class StalledQuoteItem(BaseModel):
    quotation_id: UUID
    quotation_number: str
    customer_id: UUID
    customer_name: str
    deal_id: Optional[UUID] = None
    status: str
    total_amount: Decimal
    quotation_date: date
    days_inactive: int
    stall_category: str  # NEW, AGING, STALLED, CRITICAL
    stall_reason: str
    last_activity_at: Optional[datetime] = None
    last_customer_activity_at: Optional[datetime] = None
    last_internal_activity_at: Optional[datetime] = None
    recommended_next_action: str


class StalledQuotesResponse(BaseModel):
    stalled_quotes: List[StalledQuoteItem]
    total_stalled_count: int = 0
    total_stalled_value: Decimal = Decimal("0.00")
    generated_at: datetime


# Phase 55: Discount Anomaly Monitoring
class DiscountAnomalyItem(BaseModel):
    quotation_id: UUID
    quotation_number: str
    customer_id: UUID
    customer_name: str
    blended_discount_percent: Decimal
    historical_customer_avg_discount: Optional[Decimal] = None
    historical_product_avg_discount: Optional[Decimal] = None
    organization_avg_discount: Decimal
    variance_percent: Decimal
    anomaly_score: int  # 0-100
    severity: str  # NORMAL, WATCH, ANOMALOUS, CRITICAL
    insufficient_historical_data: bool = False
    sample_size: int = 0
    evidence: List[str] = []
    created_at: datetime


class DiscountAnomaliesResponse(BaseModel):
    anomalies: List[DiscountAnomalyItem]
    anomalous_count: int
    generated_at: datetime


# Phase 56: Delivery Slippage Monitoring
class DeliverySlippageItem(BaseModel):
    delivery_promise_id: Optional[UUID] = None
    quotation_id: UUID
    quotation_number: str
    customer_id: UUID
    customer_name: str
    shipment_id: Optional[UUID] = None
    backorder_id: Optional[UUID] = None
    promised_date: date
    expected_date: date
    actual_date: Optional[date] = None
    slippage_days: int
    status: str  # ON_TRACK, AT_RISK, DELAYED, DELIVERED, UNKNOWN
    root_cause: str
    evidence: List[str] = []


class DeliverySlippageResponse(BaseModel):
    deliveries: List[DeliverySlippageItem]
    at_risk_count: int
    delayed_count: int
    generated_at: datetime


# Phase 57: Nudges & Escalations
class NudgeHistoryResponse(BaseModel):
    id: UUID
    nudge_id: UUID
    from_status: Optional[str] = None
    to_status: str
    actor_id: Optional[UUID] = None
    actor_name: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class NudgeResponse(BaseModel):
    id: UUID
    organization_id: UUID
    nudge_type: str
    severity: str
    title: str
    message: str
    entity_type: str
    entity_id: UUID
    status: str
    assigned_user_id: Optional[UUID] = None
    acknowledged_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    dismissed_at: Optional[datetime] = None
    escalated_at: Optional[datetime] = None
    action_payload: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime
    history: List[NudgeHistoryResponse] = []
    model_config = ConfigDict(from_attributes=True)


class NudgeActionRequest(BaseModel):
    notes: Optional[str] = None


# Phase 58: Reporting Engine
class ReportDomainSales(BaseModel):
    total_pipeline_value: Decimal
    weighted_pipeline_value: Decimal
    won_revenue: Decimal
    lost_revenue: Decimal
    win_rate_percent: Decimal
    average_deal_value: Decimal
    sales_cycle_days: Decimal
    open_deal_count: int
    won_deal_count: int
    lost_deal_count: int


class ReportDomainQuotations(BaseModel):
    total_quotations_count: int
    draft_count: int
    sent_count: int
    accepted_count: int
    rejected_count: int
    expired_count: int
    conversion_rate_percent: Decimal
    average_quotation_value: Decimal


class ReportDomainCommercial(BaseModel):
    gross_revenue: Decimal
    gross_margin: Decimal
    gross_margin_percent: Decimal
    discount_total: Decimal
    average_discount_percent: Decimal
    high_risk_quotation_count: int
    pending_approval_count: int


class ReportDomainFulfillment(BaseModel):
    total_stock_value: Decimal
    reserved_stock_value: Decimal
    active_shipment_count: int
    open_backorder_count: int
    on_time_delivery_rate_percent: Decimal
    average_slippage_days: Decimal


class ReportDomainBilling(BaseModel):
    total_invoiced: Decimal
    total_collected: Decimal
    outstanding_receivables: Decimal
    overdue_receivables: Decimal
    total_credits_issued: Decimal
    total_refunds_processed: Decimal


class ReportDomainSubscription(BaseModel):
    active_subscriptions_count: int
    monthly_recurring_revenue: Decimal  # MRR
    annual_recurring_revenue: Decimal   # ARR
    new_subscriptions_count: int
    cancelled_subscriptions_count: int
    churn_rate_percent: Decimal


class ExecutiveReportingSummary(BaseModel):
    period: str
    start_date: date
    end_date: date
    sales: ReportDomainSales
    quotations: ReportDomainQuotations
    commercial: ReportDomainCommercial
    fulfillment: ReportDomainFulfillment
    billing: ReportDomainBilling
    subscriptions: ReportDomainSubscription
    generated_at: datetime
