import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_user, require_admin
from app.models.user import User
from app.schemas.product import ProductCreate, ProductUpdate, ProductResponse
from app.services import products as product_service

router = APIRouter()


@router.post(
    "",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Product/Service",
    description="Creates a new Product or Service entry within the authenticated user's organization."
)
async def create_product(
    payload: ProductCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> ProductResponse:
    """Creates a new product record."""
    return await product_service.create_product(db, current_user.organization_id, payload)


@router.get(
    "",
    response_model=List[ProductResponse],
    status_code=status.HTTP_200_OK,
    summary="List Products/Services",
    description="Retrieves products belonging exclusively to the authenticated user's organization."
)
async def list_products(
    skip: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(100, ge=1, le=500, description="Pagination page limit"),
    search: Optional[str] = Query(None, min_length=1, description="Search filter in product name or SKU"),
    is_active: Optional[bool] = Query(None, description="Active status filter"),
    sku: Optional[str] = Query(None, description="Exact SKU filter"),
    currency: Optional[str] = Query(None, min_length=3, max_length=3, description="Currency filter"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> List[ProductResponse]:
    """Lists products for the current organization."""
    return await product_service.list_products(
        db,
        current_user.organization_id,
        skip=skip,
        limit=limit,
        search=search,
        is_active=is_active,
        sku=sku,
        currency=currency
    )


@router.get(
    "/{product_id}",
    response_model=ProductResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Product Details",
    description="Retrieves a specific product by ID within the authenticated user's organization."
)
async def get_product(
    product_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> ProductResponse:
    """Gets product by ID."""
    return await product_service.get_product_by_id(db, current_user.organization_id, product_id)


@router.put(
    "/{product_id}",
    response_model=ProductResponse,
    status_code=status.HTTP_200_OK,
    summary="Update Product",
    description="Updates a product record within the authenticated user's organization."
)
async def update_product(
    product_id: uuid.UUID,
    payload: ProductUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> ProductResponse:
    """Updates product details."""
    return await product_service.update_product(db, current_user.organization_id, product_id, payload)


@router.delete(
    "/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Product",
    description="Deletes a product record (requires Admin role privileges)."
)
async def delete_product(
    product_id: uuid.UUID,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
) -> None:
    """Deletes a product record."""
    await product_service.delete_product(db, current_user.organization_id, product_id)
