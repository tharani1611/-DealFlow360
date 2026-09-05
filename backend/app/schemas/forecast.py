import uuid
from datetime import date
from typing import List, Optional
from pydantic import BaseModel, Field


class DealForecastItem(BaseModel):
    """Deal-level forecast prediction object."""
    deal_id: uuid.UUID
    deal_number: str
    title: str
    customer_id: uuid.UUID
    customer_name: str
    value: str
    stage: str
    base_probability: int
    adjusted_probability: int
    forecast_category: str = Field(..., description="'COMMITTED', 'UPSIDE', 'PIPELINE', 'AT_RISK'")
    health_score: int
    health_status: str
    risk_count: int
    expected_close_date: Optional[date] = None
    weighted_value: str
    forecast_value: str
    primary_positive_factor: Optional[str] = None
    primary_negative_factor: Optional[str] = None
    positive_factors: List[str] = Field(default_factory=list)
    negative_factors: List[str] = Field(default_factory=list)


class PeriodForecast(BaseModel):
    """Forecast metrics aggregated by expected close period."""
    period_key: str = Field(..., description="e.g. 'current_month', 'next_month', 'later', 'no_close_date', 'YYYY-MM'")
    period_label: str = Field(..., description="Human readable label e.g. 'Current Month'")
    open_pipeline: str = "0.00"
    weighted_pipeline: str = "0.00"
    forecast_revenue: str = "0.00"
    committed_revenue: str = "0.00"
    upside_revenue: str = "0.00"
    at_risk_revenue: str = "0.00"
    deal_count: int = 0


class ForecastConfidenceFactors(BaseModel):
    """Positive and negative contributing factors for forecast confidence."""
    positive_factors: List[str] = Field(default_factory=list)
    negative_factors: List[str] = Field(default_factory=list)


class RevenueForecastResponse(BaseModel):
    """Executive Revenue Forecast & Prediction Response."""
    open_pipeline: str = "0.00"
    weighted_pipeline: str = "0.00"
    forecast_revenue: str = "0.00"
    committed_revenue: str = "0.00"
    upside_revenue: str = "0.00"
    at_risk_revenue: str = "0.00"
    won_revenue: str = "0.00"
    lost_revenue: str = "0.00"
    confidence_score: int = Field(..., ge=0, le=100)
    confidence_label: str = Field(..., description="'HIGH CONFIDENCE', 'MODERATE CONFIDENCE', 'LOW CONFIDENCE', 'VERY LOW CONFIDENCE'")
    concentration_risk: bool = False
    periods: List[PeriodForecast] = Field(default_factory=list)
    deals: List[DealForecastItem] = Field(default_factory=list)
    confidence_factors: ForecastConfidenceFactors = Field(default_factory=ForecastConfidenceFactors)
