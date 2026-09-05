import uuid
from decimal import Decimal
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class ApprovalRuleCreate(BaseModel):
    """Payload for creating an approval rule."""
    name: str = Field(..., max_length=255)
    description: Optional[str] = None
    is_active: bool = True
    priority: int = Field(100, ge=1)
    min_discount_percent: Optional[Decimal] = Field(None, ge=Decimal("0.00"), le=Decimal("100.00"))
    max_discount_percent: Optional[Decimal] = Field(None, ge=Decimal("0.00"), le=Decimal("100.00"))
    min_margin_percent: Optional[Decimal] = Field(None)
    risk_level: Optional[str] = Field(None, description="'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'")
    quotation_value_threshold: Optional[Decimal] = Field(None, ge=Decimal("0.00"))
    approval_level: int = Field(1, ge=1)
    required_role: str = Field("admin", max_length=50)

    model_config = ConfigDict(from_attributes=True)


class ApprovalRuleUpdate(BaseModel):
    """Payload for updating an approval rule."""
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    priority: Optional[int] = Field(None, ge=1)
    min_discount_percent: Optional[Decimal] = None
    max_discount_percent: Optional[Decimal] = None
    min_margin_percent: Optional[Decimal] = None
    risk_level: Optional[str] = None
    quotation_value_threshold: Optional[Decimal] = None
    approval_level: Optional[int] = Field(None, ge=1)
    required_role: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ApprovalRuleResponse(BaseModel):
    """Response model for an approval rule."""
    id: uuid.UUID
    organization_id: uuid.UUID
    name: str
    description: Optional[str] = None
    is_active: bool
    priority: int
    min_discount_percent: Optional[Decimal] = None
    max_discount_percent: Optional[Decimal] = None
    min_margin_percent: Optional[Decimal] = None
    risk_level: Optional[str] = None
    quotation_value_threshold: Optional[Decimal] = None
    approval_level: int
    required_role: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ApprovalDecisionRequest(BaseModel):
    """Payload for submitting an approval decision (Approve / Reject)."""
    decision: str = Field(..., description="'APPROVED' or 'REJECTED'")
    note: Optional[str] = Field(None, max_length=1000, description="Approver note or decision rationale")

    model_config = ConfigDict(from_attributes=True)


class QuotationApprovalResponse(BaseModel):
    """Response model for quotation approval status and history."""
    id: uuid.UUID
    organization_id: uuid.UUID
    quotation_id: uuid.UUID
    approval_rule_id: Optional[uuid.UUID] = None
    requested_by_user_id: uuid.UUID
    requested_by_user_name: Optional[str] = None
    approved_by_user_id: Optional[uuid.UUID] = None
    approved_by_user_name: Optional[str] = None
    status: str  # NOT_REQUIRED, PENDING, APPROVED, REJECTED, INVALIDATED
    approval_level: int
    reasons: Optional[str] = None
    decision_note: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
