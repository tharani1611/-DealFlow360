from uuid import UUID
from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field


class PortalLoginRequest(BaseModel):
    email: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)


class PortalUserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID
    customer_id: UUID
    contact_id: Optional[UUID] = None
    email: str
    full_name: str
    is_active: bool
    last_login_at: Optional[datetime] = None


class PortalTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    portal_user: PortalUserResponse


class PortalQuotationItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    product_id: UUID
    product_name: Optional[str] = None
    sku: Optional[str] = None
    quantity: Decimal
    unit_price: Decimal
    discount_percent: Decimal
    line_total: Decimal
    notes: Optional[str] = None


class PortalQuotationDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    quotation_number: str
    customer_id: UUID
    customer_name: Optional[str] = None
    status: str
    issue_date: Optional[datetime] = None
    expiration_date: Optional[datetime] = None
    subtotal: Decimal
    discount_amount: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    currency: str = "USD"
    notes: Optional[str] = None
    items: List[PortalQuotationItemResponse] = []
    created_at: datetime


class PortalQuotationListItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    quotation_number: str
    status: str
    issue_date: Optional[datetime] = None
    expiration_date: Optional[datetime] = None
    total_amount: Decimal
    currency: str = "USD"
    created_at: datetime


class PortalAcceptRejectRequest(BaseModel):
    reason: Optional[str] = None


class PortalActionResponse(BaseModel):
    success: bool
    message: str
    quotation_id: UUID
    status: str
