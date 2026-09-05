from uuid import UUID
from datetime import datetime, date
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class PaymentCreateRequest(BaseModel):
    invoice_id: UUID
    payment_date: Optional[date] = None
    amount: Decimal = Field(..., gt=0, description="Payment amount must be greater than zero")
    method: str = Field(default="BANK_TRANSFER", description="BANK_TRANSFER, CARD, CASH, CHEQUE, UPI, OTHER")
    notes: Optional[str] = None


class PaymentResponse(BaseModel):
    id: UUID
    organization_id: UUID
    payment_reference: str
    invoice_id: UUID
    customer_id: UUID
    payment_date: date
    amount: Decimal
    method: str
    status: str
    notes: Optional[str] = None
    created_by_user_id: Optional[UUID] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
