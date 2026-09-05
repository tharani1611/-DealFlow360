import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class QuotationTransitionRequest(BaseModel):
    """Payload for transitioning quotation status."""
    target_status: str = Field(..., description="Target status for transition (draft, priced, sent, accepted, rejected, expired, cancelled, converted)")
    reason: Optional[str] = Field(None, max_length=1000, description="Optional audit reason or notes for state transition")

    model_config = ConfigDict(from_attributes=True)


class QuotationStateHistoryResponse(BaseModel):
    """Response model for quotation state transition audit history."""
    id: uuid.UUID
    organization_id: uuid.UUID
    quotation_id: uuid.UUID
    from_status: Optional[str] = None
    to_status: str
    changed_by_user_id: Optional[uuid.UUID] = None
    changed_by_user_name: Optional[str] = None
    reason: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
