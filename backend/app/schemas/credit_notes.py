from uuid import UUID
from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field


class CreditNoteItemCreate(BaseModel):
    description: str
    quantity: Decimal = Field(default=Decimal("1.00"), gt=0)
    unit_price: Decimal = Field(..., ge=0)


class CreditNoteItemResponse(BaseModel):
    id: UUID
    organization_id: UUID
    credit_note_id: UUID
    description: str
    quantity: Decimal
    unit_price: Decimal
    amount: Decimal
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class CreditNoteCreateRequest(BaseModel):
    invoice_id: UUID
    reason: str = Field(..., min_length=3)
    items: List[CreditNoteItemCreate] = Field(..., min_length=1)


class CreditNoteResponse(BaseModel):
    id: UUID
    organization_id: UUID
    credit_note_number: str
    invoice_id: UUID
    customer_id: UUID
    reason: str
    subtotal: Decimal
    tax_total: Decimal
    total: Decimal
    status: str
    items: List[CreditNoteItemResponse] = []
    created_by_user_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class PaymentRefundCreateRequest(BaseModel):
    payment_id: UUID
    credit_note_id: Optional[UUID] = None
    amount: Decimal = Field(..., gt=0)
    reason: str = Field(..., min_length=3)
    refund_date: Optional[date] = None


class PaymentRefundResponse(BaseModel):
    id: UUID
    organization_id: UUID
    refund_number: str
    payment_id: UUID
    credit_note_id: Optional[UUID] = None
    amount: Decimal
    reason: str
    refund_date: date
    status: str
    created_by_user_id: Optional[UUID] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
