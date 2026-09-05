import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator
from app.schemas.ai import AIMetadata


class CopilotIntentEnum(str, Enum):
    """Supported intent categories for Sales Copilot query routing."""
    PIPELINE = "PIPELINE"
    DEAL = "DEAL"
    CUSTOMER = "CUSTOMER"
    QUOTATION = "QUOTATION"
    PRICING = "PRICING"
    MARGIN = "MARGIN"
    DISCOUNT = "DISCOUNT"
    APPROVAL = "APPROVAL"
    ACTIVITY = "ACTIVITY"
    GENERAL_SALES = "GENERAL_SALES"


class CopilotEvidenceItem(BaseModel):
    """Structured evidence item validating source facts for Copilot answers."""
    entity_type: str = Field(..., description="'deal', 'customer', 'quotation', 'approval', 'policy', 'activity'")
    entity_id: Optional[uuid.UUID] = None
    label: str = Field(..., description="Short summary label of the evidence (e.g. 'Margin %')")
    value: str = Field(..., description="Factual value (e.g. '18.5%', '₹8,50,000')")
    detail: Optional[str] = Field(None, description="Additional context or explanation")


class CopilotRequest(BaseModel):
    """Request payload for Sales Copilot natural language inquiries."""
    message: str = Field(..., min_length=1, max_length=2000, description="User question or instruction")
    deal_id: Optional[uuid.UUID] = Field(None, description="Optional scoped deal context")
    customer_id: Optional[uuid.UUID] = Field(None, description="Optional scoped customer context")
    quotation_id: Optional[uuid.UUID] = Field(None, description="Optional scoped quotation context")

    @field_validator("message")
    @classmethod
    def validate_message_non_empty(cls, v: str) -> str:
        val = v.strip()
        if not val:
            raise ValueError("Message cannot be blank or empty whitespace")
        return val


class CopilotResponse(BaseModel):
    """Structured response from AI Sales Copilot."""
    answer: str = Field(..., description="Synthesized natural language answer grounded in DealFlow360 data")
    intent: CopilotIntentEnum = Field(CopilotIntentEnum.GENERAL_SALES, description="Detected query intent category")
    evidence: List[CopilotEvidenceItem] = Field(default_factory=list, description="Source telemetry evidence items")
    recommendations: List[str] = Field(default_factory=list, description="Actionable sales recommendations")
    referenced_deal_ids: List[uuid.UUID] = Field(default_factory=list)
    referenced_customer_ids: List[uuid.UUID] = Field(default_factory=list)
    referenced_quotation_ids: List[uuid.UUID] = Field(default_factory=list)
    metadata: AIMetadata


class DealQARequest(BaseModel):
    """Request payload for natural language questions on a specific deal."""
    question: str = Field(..., min_length=1, max_length=1000, description="Question about the deal")

    @field_validator("question")
    @classmethod
    def validate_question_non_empty(cls, v: str) -> str:
        val = v.strip()
        if not val:
            raise ValueError("Question cannot be blank")
        return val


class DealQAResponse(BaseModel):
    """Response payload for deal-specific natural language Q&A."""
    deal_id: uuid.UUID
    question: str
    answer: str
    key_facts: List[str] = Field(default_factory=list)
    recommended_action: Optional[str] = None
    metadata: AIMetadata
