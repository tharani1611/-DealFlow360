import uuid
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from app.schemas.ai import AIMetadata


class RiskFactor(BaseModel):
    """Structured representation of an evaluated deal risk factor."""
    code: str = Field(..., description="Machine-readable risk code (e.g., 'OVERDUE_ACTIVITY')")
    severity: str = Field(..., description="Severity level ('low', 'medium', 'high', 'critical')")
    title: str = Field(..., description="Human-readable risk title")
    description: str = Field(..., description="Detailed explanation of the risk condition")
    recommendation: str = Field(..., description="Suggested corrective action")


class DealHealthMetrics(BaseModel):
    """Deterministic supporting telemetry for deal health."""
    probability: int = 0
    overdue_activity_count: int = 0
    days_until_expected_close: Optional[int] = None
    recent_activity_count: int = 0
    has_accepted_quotation: bool = False
    has_expired_or_rejected_quotation: bool = False


class DealHealthResponse(BaseModel):
    """Response structure for Deal Health score and risk telemetry."""
    deal_id: uuid.UUID
    deal_number: str
    title: str
    health_score: int = Field(..., ge=0, le=100, description="Deterministic deal health score (0-100)")
    health_status: str = Field(..., description="Health classification ('healthy', 'stable', 'at_risk', 'critical')")
    risk_level: str = Field(..., description="Overall risk level ('low', 'medium', 'high', 'critical')")
    risk_factors: List[RiskFactor] = Field(default_factory=list)
    metrics: DealHealthMetrics
    ai_explanation: Optional[str] = Field(None, description="Natural language AI explanation of score & risks")
    metadata: Optional[AIMetadata] = None


class CustomerEngagementMetrics(BaseModel):
    """Deterministic telemetry for customer relationship engagement."""
    last_activity_at: Optional[datetime] = None
    recent_activity_count_30d: int = 0
    overdue_activity_count: int = 0
    open_deal_count: int = 0
    total_open_deal_value: str = "0.00"
    accepted_quotation_count: int = 0


class CustomerEngagementResponse(BaseModel):
    """Response structure for Customer Engagement Telemetry."""
    customer_id: uuid.UUID
    customer_name: str
    engagement_score: int = Field(..., ge=0, le=100, description="Deterministic engagement score (0-100)")
    engagement_status: str = Field(..., description="Status ('highly_engaged', 'engaged', 'cooling', 'cold')")
    is_going_cold: bool = Field(False, description="Flag indicating customer relationship is cooling or cold")
    metrics: CustomerEngagementMetrics
    risk_reasons: List[str] = Field(default_factory=list)
    ai_explanation: Optional[str] = Field(None, description="AI summary of relationship engagement")
    metadata: Optional[AIMetadata] = None


class SalesBriefingResponse(BaseModel):
    """Executive Sales & Account Briefing payload."""
    customer_id: uuid.UUID
    customer_name: str
    primary_contact_name: Optional[str] = None
    primary_contact_email: Optional[str] = None
    relationship_status: str
    engagement_score: int
    open_pipeline_value: str
    active_deals_count: int
    overdue_activities_count: int
    deal_health_summary: List[Dict[str, Any]] = Field(default_factory=list)
    attention_items: List[str] = Field(default_factory=list)
    talking_points: List[str] = Field(default_factory=list)
    suggested_next_actions: List[Dict[str, Any]] = Field(default_factory=list)
    suggested_followup_message: Optional[str] = None
    metadata: Optional[AIMetadata] = None


class StageDistributionItem(BaseModel):
    """Pipeline distribution breakdown per sales stage."""
    stage: str
    count: int
    total_value: str
    weighted_value: str


class PipelineConcentration(BaseModel):
    """Concentration analytics evaluating risk of pipeline value clustering."""
    top_deals_value_ratio: float = Field(0.0, description="Percentage of total open value from top 2 deals")
    is_concentrated: bool = Field(False, description="True if top 2 deals account for > 50% of open value")
    top_deals_count: int = 2
    recommendation: str = Field("Diversify pipeline velocity", description="Actionable recommendation")


class PipelineMetrics(BaseModel):
    """Deterministic aggregate pipeline financial telemetry."""
    open_pipeline_value: str = "0.00"
    weighted_pipeline_value: str = "0.00"
    won_pipeline_value: str = "0.00"
    lost_pipeline_value: str = "0.00"
    at_risk_pipeline_value: str = "0.00"
    win_rate: str = "0%"
    average_deal_value: str = "0.00"
    forecast_confidence_label: str = Field("CRM-derived estimate", description="Label explaining forecast basis")
    concentration: PipelineConcentration = Field(default_factory=PipelineConcentration)
    stage_breakdown: List[StageDistributionItem] = Field(default_factory=list)


class DashboardIntelligenceResponse(BaseModel):
    """Executive CRM Intelligence Dashboard aggregate response."""
    pipeline: PipelineMetrics
    deal_health_counts: Dict[str, int] = Field(default_factory=dict)
    deals_at_risk: List[DealHealthResponse] = Field(default_factory=list)
    customers_going_cold: List[CustomerEngagementResponse] = Field(default_factory=list)
    needs_attention_count: int = 0


# Phase 15 Additions
class AttentionItem(BaseModel):
    """Structured actionable Sales Attention Center item."""
    id: str
    type: str = Field(..., description="Item type: 'activity_overdue', 'deal_risk', 'customer_cooling', 'deal_closing', 'quotation_pending', 'deal_stalled'")
    priority: str = Field(..., description="Priority: 'critical', 'high', 'medium', 'low'")
    title: str
    description: str
    entity_type: str = Field(..., description="'deal', 'customer', 'quotation', 'activity'")
    entity_id: uuid.UUID
    action_label: str


class AttentionCenterResponse(BaseModel):
    """Response structure for Sales Attention Center items."""
    items: List[AttentionItem] = Field(default_factory=list)
    critical_count: int = 0
    high_count: int = 0
    total_count: int = 0


class AlertNotification(BaseModel):
    """Derived in-app alert notification item for topbar header."""
    id: str
    type: str
    severity: str = Field("info", description="'critical', 'warning', 'info'")
    title: str
    message: str
    entity_type: Optional[str] = None
    entity_id: Optional[uuid.UUID] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class AlertsResponse(BaseModel):
    """In-app alert notification feed response."""
    alerts: List[AlertNotification] = Field(default_factory=list)
    unread_count: int = 0
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ActivityProductivityMetrics(BaseModel):
    """Telemetry metrics for activity productivity filters."""
    today_count: int = 0
    upcoming_7d_count: int = 0
    overdue_count: int = 0
    completed_this_week_count: int = 0
