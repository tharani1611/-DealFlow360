import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_user, require_admin
from app.models.user import User
from app.schemas.quotation import QuotationCreate, QuotationUpdate, QuotationResponse
from app.services import quotations as quotation_service

router = APIRouter()


@router.post(
    "",
    response_model=QuotationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Quotation",
    description="Creates a new Quotation with price snapshots within the authenticated user's organization."
)
async def create_quotation(
    payload: QuotationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> QuotationResponse:
    """Creates a new quotation record."""
    return await quotation_service.create_quotation(db, current_user.organization_id, payload, current_user_id=current_user.id)


@router.get(
    "",
    response_model=List[QuotationResponse],
    status_code=status.HTTP_200_OK,
    summary="List Quotations",
    description="Retrieves quotations belonging exclusively to the authenticated user's organization."
)
async def list_quotations(
    skip: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(100, ge=1, le=500, description="Pagination page limit"),
    status_filter: Optional[str] = Query(None, alias="status", description="Status filter (draft, sent, accepted, rejected, expired)"),
    customer_id: Optional[uuid.UUID] = Query(None, description="Customer UUID filter"),
    search: Optional[str] = Query(None, min_length=1, description="Search filter by quotation number"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> List[QuotationResponse]:
    """Lists quotations for the current organization."""
    return await quotation_service.list_quotations(
        db,
        current_user.organization_id,
        skip=skip,
        limit=limit,
        status=status_filter,
        customer_id=customer_id,
        search=search
    )


@router.get(
    "/{quotation_id}",
    response_model=QuotationResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Quotation Details",
    description="Retrieves a specific quotation by ID within the authenticated user's organization."
)
async def get_quotation(
    quotation_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> QuotationResponse:
    """Gets quotation by ID."""
    return await quotation_service.get_quotation_by_id(db, current_user.organization_id, quotation_id)


@router.put(
    "/{quotation_id}",
    response_model=QuotationResponse,
    status_code=status.HTTP_200_OK,
    summary="Update Quotation",
    description="Updates a quotation record within the authenticated user's organization."
)
async def update_quotation(
    quotation_id: uuid.UUID,
    payload: QuotationUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> QuotationResponse:
    """Updates quotation details."""
    return await quotation_service.update_quotation(db, current_user.organization_id, quotation_id, payload, current_user_id=current_user.id)


@router.delete(
    "/{quotation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Quotation",
    description="Deletes a quotation record and its items (requires Admin role privileges)."
)
async def delete_quotation(
    quotation_id: uuid.UUID,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
) -> None:
    """Deletes a quotation record."""
    await quotation_service.delete_quotation(db, current_user.organization_id, quotation_id)
