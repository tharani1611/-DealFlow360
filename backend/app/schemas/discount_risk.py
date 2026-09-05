import uuid
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class RiskFactor(BaseModel):
    """Explainable risk factor contributing to commercial risk classification."""
    code: str
    title: str
    description: str
    severity: str  # LOW, MEDIUM, HIGH, CRITICAL
    score_impact: int


class RiskEvaluationResult(BaseModel):
    """Overall evaluation result from Blended Discount Risk Engine (Phase 24)."""
    risk_level: str  # LOW, MEDIUM, HIGH, CRITICAL
    risk_score: int  # 0 to 100
    blended_discount_percent: Decimal
    overall_margin_percent: Decimal
    has_negative_margin: bool
    has_manual_override: bool
    has_policy_violation: bool
    risk_factors: List[RiskFactor]
    explanation: str

    model_config = ConfigDict(from_attributes=True)
