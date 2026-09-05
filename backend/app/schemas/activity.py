import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator

VALID_TYPES = {"task", "call", "meeting", "note", "follow_up"}
VALID_PRIORITIES = {"low", "medium", "high", "urgent"}
VALID_STATUSES = {"pending", "completed", "cancelled"}


class ActivityCreate(BaseModel):
    """Input payload for creating a new Activity."""
    activity_type: str = Field(..., description="Activity type ('task', 'call', 'meeting', 'note', 'follow_up')")
    title: str = Field(..., min_length=1, max_length=255, description="Activity subject or title")
    description: Optional[str] = Field(None, description="Detailed activity description")
    priority: Optional[str] = Field("medium", description="Priority level ('low', 'medium', 'high', 'urgent')")
    customer_id: Optional[uuid.UUID] = Field(None, description="Optional Customer UUID")
    contact_id: Optional[uuid.UUID] = Field(None, description="Optional Contact UUID")
    deal_id: Optional[uuid.UUID] = Field(None, description="Optional Deal UUID")
    quotation_id: Optional[uuid.UUID] = Field(None, description="Optional Quotation UUID")
    assigned_to_user_id: Optional[uuid.UUID] = Field(None, description="Optional assignee User UUID within organization")
    due_at: Optional[datetime] = Field(None, description="Due date and time")

    @field_validator("title")
    @classmethod
    def validate_title_non_empty(cls, v: str) -> str:
        val = v.strip()
        if not val:
            raise ValueError("Title cannot be blank or empty whitespace")
        return val

    @field_validator("activity_type")
    @classmethod
    def validate_activity_type(cls, v: str) -> str:
        val = v.strip().lower()
        if val not in VALID_TYPES:
            raise ValueError(f"activity_type must be one of: {', '.join(sorted(VALID_TYPES))}")
        return val

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return "medium"
        val = v.strip().lower()
        if val not in VALID_PRIORITIES:
            raise ValueError(f"priority must be one of: {', '.join(sorted(VALID_PRIORITIES))}")
        return val


class ActivityUpdate(BaseModel):
    """Input payload for updating an existing Activity."""
    activity_type: Optional[str] = Field(None, description="Activity type ('task', 'call', 'meeting', 'note', 'follow_up')")
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    priority: Optional[str] = Field(None, description="Priority level ('low', 'medium', 'high', 'urgent')")
    customer_id: Optional[uuid.UUID] = None
    contact_id: Optional[uuid.UUID] = None
    deal_id: Optional[uuid.UUID] = None
    quotation_id: Optional[uuid.UUID] = None
    assigned_to_user_id: Optional[uuid.UUID] = None
    due_at: Optional[datetime] = None

    @field_validator("title")
    @classmethod
    def validate_title_optional(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        val = v.strip()
        if not val:
            raise ValueError("Title cannot be blank or empty whitespace")
        return val

    @field_validator("activity_type")
    @classmethod
    def validate_type_optional(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        val = v.strip().lower()
        if val not in VALID_TYPES:
            raise ValueError(f"activity_type must be one of: {', '.join(sorted(VALID_TYPES))}")
        return val

    @field_validator("priority")
    @classmethod
    def validate_priority_optional(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        val = v.strip().lower()
        if val not in VALID_PRIORITIES:
            raise ValueError(f"priority must be one of: {', '.join(sorted(VALID_PRIORITIES))}")
        return val


class ActivityResponse(BaseModel):
    """Output payload for an Activity."""
    id: uuid.UUID
    organization_id: uuid.UUID
    activity_type: str
    title: str
    description: Optional[str] = None
    status: str
    priority: str
    customer_id: Optional[uuid.UUID] = None
    contact_id: Optional[uuid.UUID] = None
    deal_id: Optional[uuid.UUID] = None
    quotation_id: Optional[uuid.UUID] = None
    assigned_to_user_id: Optional[uuid.UUID] = None
    created_by_user_id: uuid.UUID
    due_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
