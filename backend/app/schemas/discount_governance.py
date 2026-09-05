import uuid
from decimal import Decimal
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class DiscountPolicyCreate(BaseModel):
    """Payload for creating a discount governance policy."""
    name: str = Field(..., max_length=255)
    description: Optional[str] = None
    is_active: bool = True
    priority: int = Field(100, ge=1)
    scope: str = Field("organization", description="Scope level: 'user', 'customer', 'product', 'role', 'organization'")
    product_id: Optional[uuid.UUID] = None
    customer_id: Optional[uuid.UUID] = None
    user_id: Optional[uuid.UUID] = None
    role: Optional[str] = None
    max_discount_percent: Optional[Decimal] = Field(None, ge=Decimal("0.00"), le=Decimal("100.00"))
    max_discount_amount: Optional[Decimal] = Field(None, ge=Decimal("0.00"))
    minimum_unit_price: Optional[Decimal] = Field(None, ge=Decimal("0.00"))
    minimum_margin_percent: Optional[Decimal] = Field(None)
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class DiscountPolicyUpdate(BaseModel):
    """Payload for updating a discount governance policy."""
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    priority: Optional[int] = Field(None, ge=1)
    scope: Optional[str] = None
    product_id: Optional[uuid.UUID] = None
    customer_id: Optional[uuid.UUID] = None
    user_id: Optional[uuid.UUID] = None
    role: Optional[str] = None
    max_discount_percent: Optional[Decimal] = None
    max_discount_amount: Optional[Decimal] = None
    minimum_unit_price: Optional[Decimal] = None
    minimum_margin_percent: Optional[Decimal] = None
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class DiscountPolicyResponse(BaseModel):
    """Response model for a discount governance policy."""
    id: uuid.UUID
    organization_id: uuid.UUID
    name: str
    description: Optional[str] = None
    is_active: bool
    priority: int
    scope: str
    product_id: Optional[uuid.UUID] = None
    customer_id: Optional[uuid.UUID] = None
    user_id: Optional[uuid.UUID] = None
    role: Optional[str] = None
    max_discount_percent: Optional[Decimal] = None
    max_discount_amount: Optional[Decimal] = None
    minimum_unit_price: Optional[Decimal] = None
    minimum_margin_percent: Optional[Decimal] = None
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class GovernanceViolation(BaseModel):
    """Detailed violation explanation when a discount violates a governance policy."""
    rule_id: Optional[uuid.UUID] = None
    rule_name: Optional[str] = None
    violation_type: str  # MAX_DISCOUNT_PERCENT, MAX_DISCOUNT_AMOUNT, MINIMUM_UNIT_PRICE, MINIMUM_MARGIN_PERCENT
    message: str
    product_id: Optional[uuid.UUID] = None
    product_name: Optional[str] = None
    requested_val: str
    policy_limit_val: str


class GovernanceEvaluationResult(BaseModel):
    """Overall evaluation result from Discount Governance (Phase 23)."""
    compliant: bool
    status: str  # WITHIN_POLICY, OUTSIDE_POLICY, NO_POLICY
    blended_discount_percent: Decimal
    applied_policies_count: int
    violations: List[GovernanceViolation]
    explanation: str

    model_config = ConfigDict(from_attributes=True)
