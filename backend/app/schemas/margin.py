import uuid
from decimal import Decimal
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field, field_validator


class MarginCalculateItemInput(BaseModel):
    """Input payload for a single item in a margin preview calculation."""
    product_id: uuid.UUID = Field(..., description="Target Product UUID")
    quantity: Decimal = Field(Decimal("1.00"), gt=Decimal("0.00"), description="Item quantity (must be > 0)")
    manual_unit_price: Optional[Decimal] = Field(None, ge=Decimal("0.00"), description="Optional manual selling price override")
    manual_unit_cost: Optional[Decimal] = Field(None, ge=Decimal("0.00"), description="Optional manual cost basis override")


class MarginCalculateRequest(BaseModel):
    """Payload schema for calculating multi-item margin preview."""
    customer_id: Optional[uuid.UUID] = Field(None, description="Optional Customer UUID context for customer/contract pricing rules")
    quotation_date: Optional[datetime] = Field(None, description="Effective date context (defaults to UTC now)")
    currency: Optional[str] = Field("USD", description="3-letter currency code")
    items: List[MarginCalculateItemInput] = Field(..., min_length=1, description="List of line items to evaluate for margin")


class LineMarginResponse(BaseModel):
    """Detailed margin breakdown for an individual line item."""
    product_id: uuid.UUID
    product_name: str
    quantity: Decimal
    unit_selling_price: Decimal
    unit_cost: Decimal
    line_revenue: Decimal
    line_cost: Decimal
    gross_margin: Decimal
    margin_percent: Decimal
    health_status: str = Field(..., description="'HEALTHY', 'CAUTION', 'AT_RISK', or 'NEGATIVE'")
    pricing_source: str
    explanation: str

    model_config = ConfigDict(from_attributes=True)


class QuotationMarginResponse(BaseModel):
    """Overall margin breakdown for a quotation or multi-item quote preview."""
    quotation_id: Optional[uuid.UUID] = None
    quotation_number: Optional[str] = None
    customer_id: Optional[uuid.UUID] = None
    currency: str = "USD"
    total_revenue: Decimal = Field(..., description="Total line revenue (excluding tax)")
    total_cost: Decimal = Field(..., description="Total line cost")
    gross_margin: Decimal = Field(..., description="Total gross margin (total_revenue - total_cost)")
    margin_percent: Decimal = Field(..., description="Weighted margin percentage ((gross_margin / total_revenue) * 100)")
    health_status: str = Field(..., description="Overall health classification ('HEALTHY', 'CAUTION', 'AT_RISK', 'NEGATIVE')")
    items: List[LineMarginResponse] = Field(default_factory=list)
    explanation: str

    model_config = ConfigDict(from_attributes=True)
