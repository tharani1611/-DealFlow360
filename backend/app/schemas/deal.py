import uuid
from decimal import Decimal
from datetime import date, datetime
from typing import Optional, List, Dict
from pydantic import BaseModel, ConfigDict, Field, field_validator

VALID_STAGES = {"new", "qualified", "proposal", "negotiation", "won", "lost"}
VALID_STATUSES = {"open", "won", "lost"}


class DealCreate(BaseModel):
    """Input payload for creating a new Deal."""
    customer_id: uuid.UUID = Field(..., description="Target Customer UUID within the organization")
    contact_id: Optional[uuid.UUID] = Field(None, description="Optional Contact UUID (must belong to Customer)")
    quotation_id: Optional[uuid.UUID] = Field(None, description="Optional Quotation UUID (must belong to Customer)")
    title: str = Field(..., min_length=1, max_length=255, description="Deal title / deal name")
    description: Optional[str] = Field(None, description="Detailed deal description")
    stage: Optional[str] = Field("new", description="Pipeline stage ('new', 'qualified', 'proposal', 'negotiation', 'won', 'lost')")
    value: Decimal = Field(Decimal("0.00"), ge=Decimal("0.00"), description="Deal monetary value (>= 0.00)")
    probability: Optional[int] = Field(None, ge=0, le=100, description="Win probability percentage (0-100)")
    expected_close_date: Optional[date] = Field(None, description="Target close date")
    lost_reason: Optional[str] = Field(None, description="Reason for losing the deal (required if stage is 'lost')")
    notes: Optional[str] = Field(None, description="Internal notes")

    @field_validator("title")
    @classmethod
    def validate_title_non_empty(cls, v: str) -> str:
        val = v.strip()
        if not val:
            raise ValueError("Title cannot be blank or empty whitespace")
        return val

    @field_validator("stage")
    @classmethod
    def validate_stage(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return "new"
        val = v.strip().lower()
        if val not in VALID_STAGES:
            raise ValueError(f"Stage must be one of: {', '.join(sorted(VALID_STAGES))}")
        return val


class DealUpdate(BaseModel):
    """Input payload for updating an existing Deal."""
    customer_id: Optional[uuid.UUID] = None
    contact_id: Optional[uuid.UUID] = None
    quotation_id: Optional[uuid.UUID] = None
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    stage: Optional[str] = Field(None, description="Updated stage ('new', 'qualified', 'proposal', 'negotiation', 'won', 'lost')")
    status: Optional[str] = Field(None, description="Updated status ('open', 'won', 'lost')")
    value: Optional[Decimal] = Field(None, ge=Decimal("0.00"))
    probability: Optional[int] = Field(None, ge=0, le=100)
    expected_close_date: Optional[date] = None
    lost_reason: Optional[str] = None
    notes: Optional[str] = None

    @field_validator("title")
    @classmethod
    def validate_title_optional(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        val = v.strip()
        if not val:
            raise ValueError("Title cannot be blank or empty whitespace")
        return val

    @field_validator("stage")
    @classmethod
    def validate_stage_optional(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        val = v.strip().lower()
        if val not in VALID_STAGES:
            raise ValueError(f"Stage must be one of: {', '.join(sorted(VALID_STAGES))}")
        return val

    @field_validator("status")
    @classmethod
    def validate_status_optional(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        val = v.strip().lower()
        if val not in VALID_STATUSES:
            raise ValueError(f"Status must be one of: {', '.join(sorted(VALID_STATUSES))}")
        return val


class DealResponse(BaseModel):
    """Output payload for a Deal."""
    id: uuid.UUID
    organization_id: uuid.UUID
    customer_id: uuid.UUID
    contact_id: Optional[uuid.UUID] = None
    quotation_id: Optional[uuid.UUID] = None
    title: str
    description: Optional[str] = None
    deal_number: str
    stage: str
    status: str
    value: Decimal
    probability: int
    expected_close_date: Optional[date] = None
    lost_reason: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PipelineResponse(BaseModel):
    """Kanban Pipeline view payload containing deals grouped by stage."""
    stages: Dict[str, List[DealResponse]]
