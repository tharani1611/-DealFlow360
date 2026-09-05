import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_user, require_admin
from app.models.user import User
from app.schemas.customer import CustomerCreate, CustomerUpdate, CustomerResponse
from app.schemas.activity import ActivityResponse
from app.services import customers as customer_service
from app.services import activities as activity_service

router = APIRouter()


@router.post(
    "",
    response_model=CustomerResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Customer",
    description="Creates a new Customer record within the authenticated user's organization."
)
async def create_customer(
    payload: CustomerCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> CustomerResponse:
    """Creates a new customer record."""
    return await customer_service.create_customer(db, current_user.organization_id, payload)


@router.get(
    "",
    response_model=List[CustomerResponse],
    status_code=status.HTTP_200_OK,
    summary="List Customers",
    description="Retrieves customers belonging exclusively to the authenticated user's organization."
)
async def list_customers(
    skip: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(100, ge=1, le=500, description="Pagination page limit"),
    search: Optional[str] = Query(None, min_length=1, description="Case-insensitive name search filter"),
    is_active: Optional[bool] = Query(None, description="Active status filter"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> List[CustomerResponse]:
    """Lists customers for the current organization."""
    return await customer_service.list_customers(
        db, current_user.organization_id, skip=skip, limit=limit, search=search, is_active=is_active
    )


@router.get(
    "/{customer_id}",
    response_model=CustomerResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Customer Details",
    description="Retrieves a specific customer by ID within the authenticated user's organization."
)
async def get_customer(
    customer_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> CustomerResponse:
    """Gets customer by ID."""
    return await customer_service.get_customer_by_id(db, current_user.organization_id, customer_id)


@router.put(
    "/{customer_id}",
    response_model=CustomerResponse,
    status_code=status.HTTP_200_OK,
    summary="Update Customer",
    description="Updates a customer record within the authenticated user's organization."
)
async def update_customer(
    customer_id: uuid.UUID,
    payload: CustomerUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> CustomerResponse:
    """Updates customer details."""
    return await customer_service.update_customer(db, current_user.organization_id, customer_id, payload)


@router.delete(
    "/{customer_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Customer",
    description="Deletes a customer record (requires Admin role privileges)."
)
async def delete_customer(
    customer_id: uuid.UUID,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
) -> None:
    """Deletes a customer record."""
    await customer_service.delete_customer(db, current_user.organization_id, customer_id)


@router.get(
    "/{customer_id}/activities",
    response_model=List[ActivityResponse],
    status_code=status.HTTP_200_OK,
    summary="Get Customer Activity Timeline",
    description="Retrieves chronological activity timeline (newest first) for a specific customer."
)
async def get_customer_activities(
    customer_id: uuid.UUID,
    skip: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(100, ge=1, le=500, description="Pagination page limit"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> List[ActivityResponse]:
    """Gets customer activity timeline."""
    return await activity_service.get_customer_activities(
        db, current_user.organization_id, customer_id, skip=skip, limit=limit
    )
