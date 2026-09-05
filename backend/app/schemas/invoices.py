from uuid import UUID
from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field


class InvoiceItemBase(BaseModel):
    description: str
    quantity: Decimal = Field(default=Decimal("1.00"), gt=0)
    unit_price: Decimal = Field(default=Decimal("0.00"), ge=0)
    discount_amount: Decimal = Field(default=Decimal("0.00"), ge=0)
    tax_amount: Decimal = Field(default=Decimal("0.00"), ge=0)
    billing_type: Optional[str] = "ONE_TIME"  # ONE_TIME, RECURRING


class InvoiceItemCreate(InvoiceItemBase):
    product_id: Optional[UUID] = None
    product_variant_id: Optional[UUID] = None
    quotation_item_id: Optional[UUID] = None


class InvoiceItemResponse(InvoiceItemBase):
    id: UUID
    organization_id: UUID
    invoice_id: UUID
    product_id: Optional[UUID] = None
    product_variant_id: Optional[UUID] = None
    quotation_item_id: Optional[UUID] = None
    line_subtotal: Decimal
    line_total: Decimal
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class InvoiceCreateRequest(BaseModel):
    customer_id: UUID
    quotation_id: Optional[UUID] = None
    invoice_date: Optional[date] = None
    due_date: Optional[date] = None
    currency: Optional[str] = "USD"
    items: List[InvoiceItemCreate] = []


class InvoiceUpdateRequest(BaseModel):
    invoice_date: Optional[date] = None
    due_date: Optional[date] = None
    items: Optional[List[InvoiceItemCreate]] = None


class InvoiceResponse(BaseModel):
    id: UUID
    organization_id: UUID
    invoice_number: str
    customer_id: UUID
    quotation_id: Optional[UUID] = None
    currency: str
    invoice_date: date
    due_date: date
    subtotal: Decimal
    discount_total: Decimal
    tax_total: Decimal
    total: Decimal
    amount_paid: Decimal
    amount_due: Decimal
    status: str
    items: List[InvoiceItemResponse] = []
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)
