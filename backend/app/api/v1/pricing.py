import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_user, require_admin
from app.models.user import User
from app.schemas.pricing import (
    PricingRuleCreate, PricingRuleUpdate, PricingRuleResponse,
    PricingCalculateRequest, PricingCalculateResponse
)
from app.services import pricing as pricing_service

router = APIRouter()


@router.post(
    "/calculate",
    response_model=PricingCalculateResponse,
    status_code=status.HTTP_200_OK,
    summary="Calculate Item Pricing",
    description="Evaluates Base Product Price, Volume Tiers, Customer/Contract rules, and Promotional discounts to return a deterministic unit price calculation and explainable breakdown."
)
async def calculate_pricing(
    payload: PricingCalculateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> PricingCalculateResponse:
    """Calculates pricing for a product given quantity, customer, and date context."""
    return await pricing_service.calculate_item_price(db, current_user.organization_id, payload)


@router.post(
    "/rules",
    response_model=PricingRuleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Pricing Rule",
    description="Creates a new pricing rule (contract, customer, volume, or promotion) within the authenticated user's organization."
)
async def create_pricing_rule(
    payload: PricingRuleCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> PricingRuleResponse:
    """Creates a new pricing rule."""
    return await pricing_service.create_pricing_rule(db, current_user.organization_id, payload)


@router.get(
    "/rules",
    response_model=List[PricingRuleResponse],
    status_code=status.HTTP_200_OK,
    summary="List Pricing Rules",
    description="Retrieves pricing rules belonging exclusively to the authenticated user's organization."
)
async def list_pricing_rules(
    skip: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(100, ge=1, le=500, description="Pagination page limit"),
    product_id: Optional[uuid.UUID] = Query(None, description="Product ID filter"),
    customer_id: Optional[uuid.UUID] = Query(None, description="Customer ID filter"),
    rule_type: Optional[str] = Query(None, description="Rule type filter ('contract', 'customer', 'volume', 'promotion')"),
    is_active: Optional[bool] = Query(None, description="Active status filter"),
    search: Optional[str] = Query(None, min_length=1, description="Rule name/description search query"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> List[PricingRuleResponse]:
    """Lists pricing rules for the organization."""
    return await pricing_service.list_pricing_rules(
        db,
        current_user.organization_id,
        skip=skip,
        limit=limit,
        product_id=product_id,
        customer_id=customer_id,
        rule_type=rule_type,
        is_active=is_active,
        search=search
    )


@router.get(
    "/rules/{rule_id}",
    response_model=PricingRuleResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Pricing Rule Details",
    description="Retrieves a specific pricing rule by ID within the authenticated user's organization."
)
async def get_pricing_rule(
    rule_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> PricingRuleResponse:
    """Gets pricing rule details by ID."""
    return await pricing_service.get_pricing_rule_by_id(db, current_user.organization_id, rule_id)


@router.put(
    "/rules/{rule_id}",
    response_model=PricingRuleResponse,
    status_code=status.HTTP_200_OK,
    summary="Update Pricing Rule",
    description="Updates a pricing rule record within the authenticated user's organization."
)
async def update_pricing_rule(
    rule_id: uuid.UUID,
    payload: PricingRuleUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> PricingRuleResponse:
    """Updates pricing rule details."""
    return await pricing_service.update_pricing_rule(db, current_user.organization_id, rule_id, payload)


@router.delete(
    "/rules/{rule_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Pricing Rule",
    description="Deletes a pricing rule record (requires Admin role privileges)."
)
async def delete_pricing_rule(
    rule_id: uuid.UUID,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
) -> None:
    """Deletes a pricing rule record."""
    await pricing_service.delete_pricing_rule(db, current_user.organization_id, rule_id)
