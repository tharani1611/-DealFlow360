import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status

from app.api.deps import get_current_user, require_admin
from app.core.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.schemas.product_recommendation import (
    ProductRecommendationRuleCreate,
    ProductRecommendationRuleUpdate,
    ProductRecommendationRuleResponse,
)
from app.services import product_recommendations as rule_service

router = APIRouter()


@router.post(
    "",
    response_model=ProductRecommendationRuleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Product Recommendation Rule",
    description="Admin-only endpoint to define deterministic Upsell or Cross-sell business rules."
)
async def create_rule(
    payload: ProductRecommendationRuleCreate,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(require_admin)
):
    """Creates a new product recommendation rule for current admin's tenant."""
    rule = await rule_service.create_recommendation_rule(db, current_admin.organization_id, payload)
    return await rule_service.get_recommendation_rule(db, current_admin.organization_id, rule.id)


@router.get(
    "",
    response_model=List[ProductRecommendationRuleResponse],
    status_code=status.HTTP_200_OK,
    summary="List Product Recommendation Rules",
    description="Returns filtered product recommendation rules for tenant."
)
async def list_rules(
    rule_type: Optional[str] = Query(None, description="Filter by rule type ('upsell', 'cross_sell')"),
    source_product_id: Optional[uuid.UUID] = Query(None, description="Filter by source product ID"),
    target_product_id: Optional[uuid.UUID] = Query(None, description="Filter by target product ID"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieves list of product recommendation rules."""
    rules = await rule_service.get_recommendation_rules(
        db=db,
        organization_id=current_user.organization_id,
        rule_type=rule_type,
        source_product_id=source_product_id,
        target_product_id=target_product_id,
        is_active=is_active,
        skip=skip,
        limit=limit,
    )
    return rules


@router.get(
    "/{id}",
    response_model=ProductRecommendationRuleResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Product Recommendation Rule",
    description="Retrieves a specific recommendation rule by ID."
)
async def get_rule(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieves single recommendation rule by ID."""
    return await rule_service.get_recommendation_rule(db, current_user.organization_id, id)


@router.put(
    "/{id}",
    response_model=ProductRecommendationRuleResponse,
    status_code=status.HTTP_200_OK,
    summary="Update Product Recommendation Rule",
    description="Admin-only endpoint to update an existing recommendation rule."
)
async def update_rule(
    id: uuid.UUID,
    payload: ProductRecommendationRuleUpdate,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(require_admin)
):
    """Updates existing recommendation rule."""
    await rule_service.update_recommendation_rule(db, current_admin.organization_id, id, payload)
    return await rule_service.get_recommendation_rule(db, current_admin.organization_id, id)


@router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Product Recommendation Rule",
    description="Admin-only endpoint to delete a recommendation rule."
)
async def delete_rule(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(require_admin)
):
    """Deletes recommendation rule."""
    await rule_service.delete_recommendation_rule(db, current_admin.organization_id, id)
    return None
