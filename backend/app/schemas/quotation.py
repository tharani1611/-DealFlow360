import uuid
from decimal import Decimal
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field, field_validator


class QuotationItemCreate(BaseModel):
    """Input payload for a single quotation line item."""
    product_id: uuid.UUID = Field(..., description="Target Product UUID within the organization")
    product_variant_id: Optional[uuid.UUID] = Field(None, description="Optional Product Variant UUID for future variant compatibility")
    quantity: Decimal = Field(..., gt=Decimal("0.00"), description="Line item quantity (must be > 0)")
    unit_price: Optional[Decimal] = Field(None, ge=Decimal("0.00"), description="Optional unit price override (defaults to current Product unit_price)")
    unit_cost: Optional[Decimal] = Field(None, ge=Decimal("0.00"), description="Optional custom unit cost basis (defaults to current Product unit_cost)")
    description: Optional[str] = Field(None, description="Optional line item description")
    discount_percent: Decimal = Field(Decimal("0.00"), ge=Decimal("0.00"), le=Decimal("100.00"), description="Line-level discount percentage (0-100)")
    discount_amount: Decimal = Field(Decimal("0.00"), ge=Decimal("0.00"), description="Line-level discount amount")
    tax_rate: Decimal = Field(Decimal("0.00"), ge=Decimal("0.00"), description="Line-level tax rate percentage")
    tax_amount: Decimal = Field(Decimal("0.00"), ge=Decimal("0.00"), description="Line-level tax amount")
    sequence: int = Field(0, ge=0, description="Display sequence / line order")


class QuotationItemResponse(BaseModel):
    """Output payload for a quotation line item with historical price snapshot."""
    id: uuid.UUID
    quotation_id: uuid.UUID
    product_id: uuid.UUID
    product_variant_id: Optional[uuid.UUID] = None
    product_name: str
    sku: Optional[str] = None
    description: Optional[str] = None
    sequence: int = 0
    quantity: Decimal
    unit_price: Decimal
    unit_cost: Decimal = Decimal("0.00")
    discount_percent: Decimal = Decimal("0.00")
    discount_amount: Decimal = Decimal("0.00")
    tax_rate: Decimal = Decimal("0.00")
    tax_amount: Decimal = Decimal("0.00")
    line_total: Decimal
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class QuotationCreate(BaseModel):
    """Input payload for creating a new Quotation."""
    customer_id: uuid.UUID = Field(..., description="Target Customer UUID within the organization")
    contact_id: Optional[uuid.UUID] = Field(None, description="Optional Contact UUID within the organization and customer")
    deal_id: Optional[uuid.UUID] = Field(None, description="Optional Deal UUID within the organization and customer")
    title: Optional[str] = Field(None, description="Quotation title or subject")
    currency: str = Field("USD", max_length=3, description="Quotation ISO currency code")
    items: List[QuotationItemCreate] = Field(..., min_length=1, description="List of line items (at least 1 required)")
    quotation_date: Optional[datetime] = Field(None, description="Quotation issuance date (defaults to current time)")
    valid_until: Optional[datetime] = Field(None, description="Expiration date")
    discount_amount: Decimal = Field(Decimal("0.00"), ge=Decimal("0.00"), description="Quotation-level discount amount (>= 0)")
    tax_amount: Decimal = Field(Decimal("0.00"), ge=Decimal("0.00"), description="Quotation-level tax amount (>= 0)")
    notes: Optional[str] = Field(None, description="Terms or internal notes")
    terms: Optional[str] = Field(None, description="Commercial terms and conditions")

    @field_validator("items")
    @classmethod
    def validate_items_non_empty(cls, v: List[QuotationItemCreate]) -> List[QuotationItemCreate]:
        if not v or len(v) == 0:
            raise ValueError("Quotation must contain at least one item")
        return v

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: str) -> str:
        code = v.strip().upper()
        if len(code) != 3:
            raise ValueError("Currency code must be a 3-letter ISO code (e.g. USD, EUR, INR)")
        return code


class QuotationUpdate(BaseModel):
    """Input payload for updating an existing Quotation."""
    customer_id: Optional[uuid.UUID] = None
    contact_id: Optional[uuid.UUID] = None
    deal_id: Optional[uuid.UUID] = None
    title: Optional[str] = None
    currency: Optional[str] = None
    items: Optional[List[QuotationItemCreate]] = Field(None, min_length=1)
    status: Optional[str] = Field(None, description="Updated status ('draft', 'sent', 'accepted', 'rejected', 'expired')")
    quotation_date: Optional[datetime] = None
    valid_until: Optional[datetime] = None
    discount_amount: Optional[Decimal] = Field(None, ge=Decimal("0.00"))
    tax_amount: Optional[Decimal] = Field(None, ge=Decimal("0.00"))
    notes: Optional[str] = None
    terms: Optional[str] = None

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        valid_statuses = {"draft", "sent", "accepted", "rejected", "expired"}
        val = v.strip().lower()
        if val not in valid_statuses:
            raise ValueError(f"Status must be one of: {', '.join(sorted(valid_statuses))}")
        return val

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        code = v.strip().upper()
        if len(code) != 3:
            raise ValueError("Currency code must be a 3-letter ISO code (e.g. USD, EUR, INR)")
        return code


class QuotationResponse(BaseModel):
    """Output payload for a Quotation including line items and calculated totals."""
    id: uuid.UUID
    organization_id: uuid.UUID
    customer_id: uuid.UUID
    contact_id: Optional[uuid.UUID] = None
    deal_id: Optional[uuid.UUID] = None
    title: Optional[str] = None
    quotation_number: str
    status: str
    currency: str = "USD"
    quotation_date: datetime
    valid_until: Optional[datetime] = None
    notes: Optional[str] = None
    terms: Optional[str] = None
    created_by_user_id: Optional[uuid.UUID] = None
    updated_by_user_id: Optional[uuid.UUID] = None
    subtotal: Decimal
    discount_amount: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    items: List[QuotationItemResponse] = []
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

