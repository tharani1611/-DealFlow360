import uuid
import re
from decimal import Decimal
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator

CURRENCY_REGEX = re.compile(r"^[A-Z]{3}$")


class ProductCreate(BaseModel):
    """Payload schema for creating a new Product/Service."""
    name: str = Field(..., min_length=1, max_length=255, description="Product or service name")
    sku: str = Field(..., min_length=1, max_length=100, description="Stock Keeping Unit identifier")
    description: Optional[str] = Field(None, description="Detailed product description")
    unit_price: Decimal = Field(..., ge=Decimal("0.00"), description="Unit price (non-negative monetary decimal)")
    unit_cost: Decimal = Field(Decimal("0.00"), ge=Decimal("0.00"), description="Unit cost basis (non-negative monetary decimal)")
    currency: str = Field("USD", min_length=3, max_length=3, description="3-letter ISO currency code (e.g. USD, EUR, INR)")
    is_active: bool = Field(True, description="Product availability status flag")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("Product name cannot be empty or whitespace only")
        return stripped

    @field_validator("sku")
    @classmethod
    def validate_sku(cls, v: str) -> str:
        stripped = v.strip().upper()
        if not stripped:
            raise ValueError("Product SKU cannot be empty or whitespace only")
        return stripped

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: str) -> str:
        code = v.strip().upper()
        if not CURRENCY_REGEX.match(code):
            raise ValueError("Currency must be a 3-letter uppercase ISO code (e.g. USD, EUR)")
        return code


class ProductUpdate(BaseModel):
    """Payload schema for updating an existing Product/Service."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    sku: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    unit_price: Optional[Decimal] = Field(None, ge=Decimal("0.00"))
    unit_cost: Optional[Decimal] = Field(None, ge=Decimal("0.00"))
    currency: Optional[str] = Field(None, min_length=3, max_length=3)
    is_active: Optional[bool] = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        stripped = v.strip()
        if not stripped:
            raise ValueError("Product name cannot be empty or whitespace only")
        return stripped

    @field_validator("sku")
    @classmethod
    def validate_sku(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        stripped = v.strip().upper()
        if not stripped:
            raise ValueError("Product SKU cannot be empty or whitespace only")
        return stripped

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        code = v.strip().upper()
        if not CURRENCY_REGEX.match(code):
            raise ValueError("Currency must be a 3-letter uppercase ISO code (e.g. USD, EUR)")
        return code


class ProductResponse(BaseModel):
    """Public product response payload schema."""
    id: uuid.UUID
    organization_id: uuid.UUID
    name: str
    sku: str
    description: Optional[str] = None
    unit_price: Decimal
    unit_cost: Decimal = Decimal("0.00")
    currency: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
