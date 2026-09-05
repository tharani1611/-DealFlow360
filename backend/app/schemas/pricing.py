import uuid
from decimal import Decimal
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field, field_validator

VALID_RULE_TYPES = {"contract", "customer", "volume", "promotion"}
VALID_PRICE_TYPES = {"override_price", "percentage_discount", "fixed_discount"}


class PricingRuleCreate(BaseModel):
    """Payload schema for creating a new Pricing Rule."""
    name: str = Field(..., min_length=1, max_length=255, description="Rule display name")
    rule_type: str = Field(..., description="Rule classification: 'contract', 'customer', 'volume', or 'promotion'")
    product_id: uuid.UUID = Field(..., description="Target Product ID")
    customer_id: Optional[uuid.UUID] = Field(None, description="Optional Customer ID (required for customer/contract rules)")
    min_quantity: Decimal = Field(Decimal("1.00"), gt=Decimal("0.00"), description="Minimum quantity threshold")
    max_quantity: Optional[Decimal] = Field(None, description="Optional maximum quantity threshold (null for unbounded)")
    price_type: str = Field("override_price", description="Pricing mechanism: 'override_price', 'percentage_discount', or 'fixed_discount'")
    value: Decimal = Field(..., ge=Decimal("0.00"), description="Target unit price or discount percentage/amount")
    priority: int = Field(100, gt=0, description="Priority rank (lower value = higher precedence)")
    valid_from: Optional[datetime] = Field(None, description="Effective start date/time (UTC)")
    valid_until: Optional[datetime] = Field(None, description="Effective end date/time (UTC)")
    is_active: bool = Field(True, description="Rule active status")
    description: Optional[str] = Field(None, description="Optional internal notes/description")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("Pricing rule name cannot be empty or whitespace only")
        return stripped

    @field_validator("rule_type")
    @classmethod
    def validate_rule_type(cls, v: str) -> str:
        code = v.strip().lower()
        if code not in VALID_RULE_TYPES:
            raise ValueError(f"Invalid rule_type '{v}'. Allowed types: {sorted(list(VALID_RULE_TYPES))}")
        return code

    @field_validator("price_type")
    @classmethod
    def validate_price_type(cls, v: str) -> str:
        code = v.strip().lower()
        if code not in VALID_PRICE_TYPES:
            raise ValueError(f"Invalid price_type '{v}'. Allowed price types: {sorted(list(VALID_PRICE_TYPES))}")
        return code

    @field_validator("max_quantity")
    @classmethod
    def validate_max_quantity(cls, v: Optional[Decimal], values) -> Optional[Decimal]:
        if v is not None and v <= Decimal("0.00"):
            raise ValueError("max_quantity must be greater than zero if specified")
        return v


class PricingRuleUpdate(BaseModel):
    """Payload schema for updating an existing Pricing Rule."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    rule_type: Optional[str] = None
    product_id: Optional[uuid.UUID] = None
    customer_id: Optional[uuid.UUID] = None
    min_quantity: Optional[Decimal] = Field(None, gt=Decimal("0.00"))
    max_quantity: Optional[Decimal] = None
    price_type: Optional[str] = None
    value: Optional[Decimal] = Field(None, ge=Decimal("0.00"))
    priority: Optional[int] = Field(None, gt=0)
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None
    is_active: Optional[bool] = None
    description: Optional[str] = None

    @field_validator("rule_type")
    @classmethod
    def validate_rule_type(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        code = v.strip().lower()
        if code not in VALID_RULE_TYPES:
            raise ValueError(f"Invalid rule_type '{v}'. Allowed types: {sorted(list(VALID_RULE_TYPES))}")
        return code

    @field_validator("price_type")
    @classmethod
    def validate_price_type(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        code = v.strip().lower()
        if code not in VALID_PRICE_TYPES:
            raise ValueError(f"Invalid price_type '{v}'. Allowed price types: {sorted(list(VALID_PRICE_TYPES))}")
        return code


class PricingRuleResponse(BaseModel):
    """Public response payload schema for Pricing Rules."""
    id: uuid.UUID
    organization_id: uuid.UUID
    name: str
    rule_type: str
    product_id: uuid.UUID
    customer_id: Optional[uuid.UUID] = None
    min_quantity: Decimal
    max_quantity: Optional[Decimal] = None
    price_type: str
    value: Decimal
    priority: int
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None
    is_active: bool
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PricingCalculateRequest(BaseModel):
    """Payload schema for calculating item pricing preview."""
    product_id: uuid.UUID = Field(..., description="Target Product ID")
    quantity: Decimal = Field(Decimal("1.00"), gt=Decimal("0.00"), description="Purchase quantity")
    customer_id: Optional[uuid.UUID] = Field(None, description="Optional Customer ID context")
    quotation_date: Optional[datetime] = Field(None, description="Effective quotation date (defaults to UTC now)")
    currency: Optional[str] = Field("USD", description="Target 3-letter currency code")
    manual_unit_price: Optional[Decimal] = Field(None, ge=Decimal("0.00"), description="Optional manual unit price override")


class PricingCalculateResponse(BaseModel):
    """Explainable pricing calculation response schema."""
    base_price: Decimal = Field(..., description="Base product standard unit price")
    selected_unit_price: Decimal = Field(..., description="Unit price after rule replacement (before promo adjustments)")
    final_unit_price: Decimal = Field(..., description="Final effective unit price")
    quantity: Decimal = Field(..., description="Line item quantity")
    currency: str = Field(..., description="Monetary currency code")
    pricing_source: str = Field(..., description="Source mechanism: 'BASE_PRODUCT_PRICE', 'CONTRACT', 'CUSTOMER', 'VOLUME', 'PROMOTION', or 'MANUAL_OVERRIDE'")
    applied_rule_id: Optional[uuid.UUID] = Field(None, description="ID of primary applied pricing rule if applicable")
    applied_rule_name: Optional[str] = Field(None, description="Name of primary applied pricing rule if applicable")
    discount_amount: Decimal = Field(..., description="Total unit discount relative to base price")
    discount_percent: Decimal = Field(..., description="Effective discount percentage relative to base price")
    explanation: str = Field(..., description="Human-readable explainable pricing breakdown string")

    model_config = ConfigDict(from_attributes=True)
