from uuid import UUID
from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field


class SubscriptionCreateRequest(BaseModel):
    customer_id: UUID
    product_id: UUID
    variant_id: Optional[UUID] = None
    quotation_id: Optional[UUID] = None
    quotation_item_id: Optional[UUID] = None
    plan_name: str
    quantity: Decimal = Field(default=Decimal("1.00"), gt=0)
    unit_price: Decimal = Field(..., ge=0)
    billing_interval: str = Field(default="MONTHLY", description="MONTHLY, QUARTERLY, YEARLY")
    start_date: Optional[date] = None


class SubscriptionUpdateRequest(BaseModel):
    plan_name: Optional[str] = None
    quantity: Optional[Decimal] = Field(default=None, gt=0)
    unit_price: Optional[Decimal] = Field(default=None, ge=0)
    billing_interval: Optional[str] = None
    status: Optional[str] = None


class SubscriptionProrationRequest(BaseModel):
    new_quantity: Decimal = Field(..., gt=0)
    new_unit_price: Decimal = Field(..., ge=0)
    effective_date: Optional[date] = None
    notes: Optional[str] = None


class SubscriptionCancellationRequest(BaseModel):
    cancellation_type: str = Field(default="END_OF_PERIOD", description="IMMEDIATE, END_OF_PERIOD")
    reason: str = Field(..., min_length=3)
    notes: Optional[str] = None


class BillingScheduleResponse(BaseModel):
    id: UUID
    organization_id: UUID
    subscription_id: UUID
    billing_period_start: date
    billing_period_end: date
    billing_date: date
    amount: Decimal
    status: str
    invoice_id: Optional[UUID] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class SubscriptionProrationResponse(BaseModel):
    id: UUID
    organization_id: UUID
    subscription_id: UUID
    old_quantity: Decimal
    new_quantity: Decimal
    old_unit_price: Decimal
    new_unit_price: Decimal
    billing_period_start: date
    billing_period_end: date
    effective_date: date
    total_period_days: int
    remaining_days: int
    prorated_amount: Decimal
    actor_id: Optional[UUID] = None
    actor_name: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class SubscriptionCancellationResponse(BaseModel):
    id: UUID
    organization_id: UUID
    subscription_id: UUID
    cancellation_type: str
    reason: str
    requested_by_user_id: Optional[UUID] = None
    effective_date: date
    notes: Optional[str] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class SubscriptionResponse(BaseModel):
    id: UUID
    organization_id: UUID
    subscription_number: str
    customer_id: UUID
    quotation_id: Optional[UUID] = None
    quotation_item_id: Optional[UUID] = None
    product_id: UUID
    variant_id: Optional[UUID] = None
    plan_name: str
    quantity: Decimal
    unit_price: Decimal
    billing_interval: str
    start_date: date
    next_billing_date: date
    end_date: Optional[date] = None
    status: str
    schedules: List[BillingScheduleResponse] = []
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)
