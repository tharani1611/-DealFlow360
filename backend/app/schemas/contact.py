import uuid
import re
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")


class ContactCreate(BaseModel):
    """Payload schema for creating a new Contact person."""
    customer_id: uuid.UUID = Field(..., description="Target Customer UUID within the organization")
    first_name: str = Field(..., min_length=1, max_length=255, description="First name of the contact person")
    last_name: Optional[str] = Field(None, max_length=255, description="Last name of the contact person")
    email: Optional[str] = Field(None, max_length=255, description="Email address")
    phone: Optional[str] = Field(None, max_length=50, description="Phone number")
    job_title: Optional[str] = Field(None, max_length=255, description="Job title / role")
    is_primary: bool = Field(False, description="Primary contact flag")

    @field_validator("first_name")
    @classmethod
    def validate_first_name(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("First name cannot be empty or whitespace only")
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


class ContactUpdate(BaseModel):
    """Payload schema for updating an existing Contact."""
    customer_id: Optional[uuid.UUID] = Field(None, description="Target Customer UUID within the organization")
    first_name: Optional[str] = Field(None, min_length=1, max_length=255)
    last_name: Optional[str] = Field(None, max_length=255)
    email: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=50)
    job_title: Optional[str] = Field(None, max_length=255)
    is_primary: Optional[bool] = None

    @field_validator("first_name")
    @classmethod
    def validate_first_name(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        stripped = v.strip()
        if not stripped:
            raise ValueError("First name cannot be empty or whitespace only")
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


class ContactResponse(BaseModel):
    """Public contact response payload schema."""
    id: uuid.UUID
    organization_id: uuid.UUID
    customer_id: uuid.UUID
    first_name: str
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    job_title: Optional[str] = None
    is_primary: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
