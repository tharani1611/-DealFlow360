import uuid
from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Literal
from pydantic import BaseModel, Field, ConfigDict, model_validator


class ProductRecommendationRuleBase(BaseModel):
    """Base schema for Product Recommendation Rule."""
    source_product_id: uuid.UUID
    target_product_id: uuid.UUID
    rule_type: Literal['upsell', 'cross_sell'] = Field(..., description="Rule classification: 'upsell' or 'cross_sell'")
    priority: int = Field(5, ge=1, le=100, description="Priority rank (1 = highest priority)")
    is_active: bool = True
    min_customer_deal_count: Optional[int] = Field(None, ge=0, description="Minimum won deal count required")
    min_customer_pipeline_value: Optional[Decimal] = Field(None, ge=0, description="Minimum open pipeline value required")
    min_customer_activity_count: Optional[int] = Field(None, ge=0, description="Minimum activity count required")
    description: Optional[str] = Field(None, max_length=1000)

    @model_validator(mode='after')
    def validate_source_ne_target(self):
        if self.source_product_id == self.target_product_id:
            raise ValueError("source_product_id and target_product_id cannot be the same product.")
        return self


class ProductRecommendationRuleCreate(ProductRecommendationRuleBase):
    """Payload for creating a product recommendation rule."""
    pass


class ProductRecommendationRuleUpdate(BaseModel):
    """Payload for updating a product recommendation rule."""
    priority: Optional[int] = Field(None, ge=1, le=100)
    is_active: Optional[bool] = None
    min_customer_deal_count: Optional[int] = Field(None, ge=0)
    min_customer_pipeline_value: Optional[Decimal] = Field(None, ge=0)
    min_customer_activity_count: Optional[int] = Field(None, ge=0)
    description: Optional[str] = Field(None, max_length=1000)


class ProductRecommendationRuleResponse(BaseModel):
    """Response structure for a product recommendation rule."""
    id: uuid.UUID
    organization_id: uuid.UUID
    source_product_id: uuid.UUID
    target_product_id: uuid.UUID
    rule_type: str
    priority: int
    is_active: bool
    min_customer_deal_count: Optional[int] = None
    min_customer_pipeline_value: Optional[str] = None
    min_customer_activity_count: Optional[int] = None
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    source_product_name: Optional[str] = None
    source_product_sku: Optional[str] = None
    target_product_name: Optional[str] = None
    target_product_sku: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ProductRecommendationItem(BaseModel):
    """Structured product opportunity recommendation output."""
    product_id: uuid.UUID
    product_name: str
    sku: str
    unit_price: str
    recommendation_type: Literal['upsell', 'cross_sell']
    source_product_id: uuid.UUID
    source_product_name: str
    priority: int
    eligibility: str
    reason: str
    rule_id: uuid.UUID


class CustomerProductRecommendationsResponse(BaseModel):
    """Response payload for customer product recommendations."""
    customer_id: uuid.UUID
    customer_name: str
    recommendations: List[ProductRecommendationItem] = Field(default_factory=list)
