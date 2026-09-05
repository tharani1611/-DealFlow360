from uuid import UUID
from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict, Field


class LineCommentCreate(BaseModel):
    quotation_item_id: UUID
    comment_text: str = Field(..., min_length=1)
    is_internal_only: bool = False


class LineCommentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    quotation_id: UUID
    quotation_item_id: UUID
    author_type: str
    author_user_id: Optional[UUID] = None
    author_portal_user_id: Optional[UUID] = None
    author_name: str
    comment_text: str
    is_internal_only: bool
    created_at: datetime


class ChangeRequestCreate(BaseModel):
    quotation_item_id: Optional[UUID] = None
    change_type: str = Field(..., description="quantity_change, counter_discount, validity_extension, general_terms")
    requested_discount_percent: Optional[Decimal] = Field(None, ge=0, le=100)
    requested_quantity: Optional[Decimal] = Field(None, gt=0)
    request_details: str = Field(..., min_length=1)


class ChangeRequestReview(BaseModel):
    status: str = Field(..., description="ACCEPTED or REJECTED")
    response_note: Optional[str] = None


class ChangeRequestResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    quotation_id: UUID
    quotation_item_id: Optional[UUID] = None
    requested_by_portal_user_id: UUID
    change_type: str
    status: str
    requested_discount_percent: Optional[Decimal] = None
    requested_quantity: Optional[Decimal] = None
    request_details: str
    response_note: Optional[str] = None
    reviewed_by_user_id: Optional[UUID] = None
    reviewed_at: Optional[datetime] = None
    created_at: datetime


class CounterDiscountApply(BaseModel):
    quotation_item_id: Optional[UUID] = None
    requested_discount_percent: Decimal = Field(..., ge=0, le=100)
    change_reason: str = Field(..., min_length=1)


class QuotationVersionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    quotation_id: UUID
    version_number: int
    subtotal: Decimal
    discount_amount: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    gross_margin: Optional[Decimal] = None
    margin_percent: Optional[Decimal] = None
    change_reason: str
    snapshot_payload: Dict[str, Any]
    created_by_user_id: Optional[UUID] = None
    created_at: datetime


class ApprovalAuditLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    quotation_id: UUID
    approval_id: Optional[UUID] = None
    event_type: str
    actor_user_id: Optional[UUID] = None
    actor_name: Optional[str] = None
    previous_status: Optional[str] = None
    new_status: str
    reason: Optional[str] = None
    notes: Optional[str] = None
    approval_rule_id: Optional[UUID] = None
    approval_level: int
    created_at: datetime
