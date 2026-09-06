import uuid
import re
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator

SLUG_REGEX = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")


class OrganizationResponse(BaseModel):
    """Public organization response payload schema."""
    id: uuid.UUID
    name: str
    slug: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserResponse(BaseModel):
    """Public user response payload schema (never leaks password_hash)."""
    id: uuid.UUID
    organization_id: uuid.UUID
    email: str
    full_name: Optional[str] = None
    is_active: bool
    is_admin: bool
    role: str = Field(..., description="Effective role name ('admin' or 'user') derived from is_admin")
    created_at: datetime
    updated_at: datetime
    organization: Optional[OrganizationResponse] = None

    model_config = ConfigDict(from_attributes=True)


class RegisterRequest(BaseModel):
    """Registration payload for creating or joining an Organization with a selected role."""
    organization_name: Optional[str] = Field(None, max_length=255, description="Full legal or commercial organization name")
    organization_slug: str = Field(..., min_length=2, max_length=255, description="Unique URL-friendly organization slug")
    email: str = Field(..., min_length=3, max_length=255, description="User email address")
    full_name: Optional[str] = Field(None, max_length=255, description="User full name")
    password: str = Field(..., min_length=8, max_length=72, description="Password (min 8 chars, max 72 bytes)")
    role: Optional[str] = Field(None, description="Requested user role ('Admin', 'Sales Representative', 'Inventory Manager', 'Billing Controller')")

    @field_validator("organization_name")
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        stripped = v.strip()
        if not stripped:
            return None
        return stripped

    @field_validator("organization_slug")
    @classmethod
    def validate_slug(cls, v: str) -> str:
        slug = v.strip().lower()
        if not SLUG_REGEX.match(slug):
            raise ValueError("Organization slug must contain only lowercase letters, numbers, and hyphens (e.g. acme-corp)")
        return slug

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        email = v.strip().lower()
        if not EMAIL_REGEX.match(email):
            raise ValueError("Invalid email address format")
        return email

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Password cannot be empty or whitespace only")
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if len(v.encode("utf-8")) > 72:
            raise ValueError("Password cannot exceed 72 bytes in UTF-8 encoding")
        return v


class LoginRequest(BaseModel):
    """Organization-aware login payload."""
    organization_slug: str = Field(..., description="Organization slug identifier")
    email: str = Field(..., description="User email address")
    password: str = Field(..., description="User password")

    @field_validator("organization_slug")
    @classmethod
    def normalize_slug(cls, v: str) -> str:
        return v.strip().lower()

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return v.strip().lower()


class AuthResponse(BaseModel):
    """Authentication success payload returning JWT token and user/tenant details."""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
    organization: OrganizationResponse


class RegisterResponse(BaseModel):
    """Registration response payload containing created user, organization, and access token."""
    user: UserResponse
    organization: OrganizationResponse
    access_token: Optional[str] = None
    token_type: str = "bearer"
