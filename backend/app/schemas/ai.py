import uuid
from datetime import datetime, timezone
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


class AIMetadata(BaseModel):
    """Metadata response block for AI generated insights."""
    provider: str = Field(..., description="AI Provider name (e.g. 'gemini', 'mock')")
    model: str = Field(..., description="AI Model identifier (e.g. 'gemini-1.5-flash')")
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Timestamp of generation")


class CustomerSummaryResponse(BaseModel):
    """Structured AI response for Customer CRM relationship summary."""
    customer_id: uuid.UUID
    customer_name: str
    summary: str
    key_insights: List[str] = Field(default_factory=list)
    health_score_estimate: str = Field("good", description="Estimated relationship health ('good', 'neutral', 'at_risk')")
    metadata: AIMetadata


class DealAnalysisResponse(BaseModel):
    """Structured AI response for Deal opportunity risk & signal analysis."""
    deal_id: uuid.UUID
    deal_number: str
    summary: str
    risk_level: str = Field("medium", description="Evaluated risk level ('low', 'medium', 'high')")
    risks: List[str] = Field(default_factory=list)
    positive_signals: List[str] = Field(default_factory=list)
    recommended_actions: List[str] = Field(default_factory=list)
    metadata: AIMetadata


class NextActionResponse(BaseModel):
    """Structured AI response recommending next best CRM action for a Deal."""
    deal_id: uuid.UUID
    action_type: str = Field("follow_up", description="Recommended activity type ('task', 'call', 'meeting', 'follow_up')")
    title: str = Field(..., description="Recommended activity subject line")
    reason: str = Field(..., description="Explanation of why this action is recommended")
    priority: str = Field("medium", description="Recommended priority ('low', 'medium', 'high', 'urgent')")
    metadata: AIMetadata


class ActivityInsightResponse(BaseModel):
    """Structured AI response analyzing deal activity engagement and follow-up velocity."""
    deal_id: uuid.UUID
    summary: str
    overdue_count: int = 0
    upcoming_count: int = 0
    insights: List[str] = Field(default_factory=list)
    recommended_follow_ups: List[str] = Field(default_factory=list)
    metadata: AIMetadata


class AssistantRequest(BaseModel):
    """Input payload for general CRM assistant questions."""
    question: str = Field(..., min_length=1, max_length=1000, description="Natural language user prompt or question")

    @field_validator("question")
    @classmethod
    def validate_question_non_empty(cls, v: str) -> str:
        val = v.strip()
        if not val:
            raise ValueError("Question cannot be blank or empty whitespace")
        return val


class AssistantResponse(BaseModel):
    """Structured AI response for CRM assistant inquiries."""
    answer: str
    context_used_count: int = 0
    referenced_deal_ids: List[uuid.UUID] = Field(default_factory=list)
    metadata: AIMetadata
