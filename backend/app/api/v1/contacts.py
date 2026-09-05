import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_user, require_admin
from app.models.user import User
from app.schemas.contact import ContactCreate, ContactUpdate, ContactResponse
from app.services import contacts as contact_service

router = APIRouter()


@router.post(
    "",
    response_model=ContactResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Contact",
    description="Creates a new Contact person linked to a Customer within the authenticated user's organization."
)
async def create_contact(
    payload: ContactCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> ContactResponse:
    """Creates a new contact person."""
    return await contact_service.create_contact(db, current_user.organization_id, payload)


@router.get(
    "",
    response_model=List[ContactResponse],
    status_code=status.HTTP_200_OK,
    summary="List Contacts",
    description="Retrieves contacts belonging exclusively to the authenticated user's organization."
)
async def list_contacts(
    skip: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(100, ge=1, le=500, description="Pagination page limit"),
    customer_id: Optional[uuid.UUID] = Query(None, description="Filter contacts by Customer UUID"),
    search: Optional[str] = Query(None, min_length=1, description="Case-insensitive search in name or email"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> List[ContactResponse]:
    """Lists contacts for the current organization."""
    return await contact_service.list_contacts(
        db, current_user.organization_id, skip=skip, limit=limit, customer_id=customer_id, search=search
    )


@router.get(
    "/{contact_id}",
    response_model=ContactResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Contact Details",
    description="Retrieves a specific contact by ID within the authenticated user's organization."
)
async def get_contact(
    contact_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> ContactResponse:
    """Gets contact by ID."""
    return await contact_service.get_contact_by_id(db, current_user.organization_id, contact_id)


@router.put(
    "/{contact_id}",
    response_model=ContactResponse,
    status_code=status.HTTP_200_OK,
    summary="Update Contact",
    description="Updates a contact record within the authenticated user's organization."
)
async def update_contact(
    contact_id: uuid.UUID,
    payload: ContactUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> ContactResponse:
    """Updates contact details."""
    return await contact_service.update_contact(db, current_user.organization_id, contact_id, payload)


@router.delete(
    "/{contact_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Contact",
    description="Deletes a contact record (requires Admin role privileges)."
)
async def delete_contact(
    contact_id: uuid.UUID,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
) -> None:
    """Deletes a contact record."""
    await contact_service.delete_contact(db, current_user.organization_id, contact_id)
