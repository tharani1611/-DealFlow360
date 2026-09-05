import uuid
import re
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")


class CustomerCreate(BaseModel):
    """Payload schema for creating a new Customer."""
    name: str = Field(..., min_length=1, max_length=255, description="Customer company or commercial name")
    email: Optional[str] = Field(None, max_length=255, description="Primary email address")
    phone: Optional[str] = Field(None, max_length=50, description="Phone number")
    address: Optional[str] = Field(None, max_length=500, description="Street address")
    city: Optional[str] = Field(None, max_length=100, description="City")
    state: Optional[str] = Field(None, max_length=100, description="State/Province")
    country: Optional[str] = Field(None, max_length=100, description="Country")
    postal_code: Optional[str] = Field(None, max_length=50, description="ZIP/Postal code")
    is_active: bool = Field(True, description="Active status flag")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("Customer name cannot be empty or whitespace only")
        return stripped

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        stripped = v.strip().lower()
        if not stripped:
            return None
        if not EMAIL_REGEX.match(stripped):
            raise ValueError("Invalid email address format")
        return stripped


class CustomerUpdate(BaseModel):
    """Payload schema for updating an existing Customer."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    email: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=50)
    address: Optional[str] = Field(None, max_length=500)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    country: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=50)
    is_active: Optional[bool] = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        stripped = v.strip()
        if not stripped:
            raise ValueError("Customer name cannot be empty or whitespace only")
        return stripped

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        stripped = v.strip().lower()
        if not stripped:
            return None
        if not EMAIL_REGEX.match(stripped):
            raise ValueError("Invalid email address format")
        return stripped


class CustomerResponse(BaseModel):
    """Public customer response payload schema."""
    id: uuid.UUID
    organization_id: uuid.UUID
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    postal_code: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
