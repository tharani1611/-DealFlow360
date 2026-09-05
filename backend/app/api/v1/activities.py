import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_user, require_admin
from app.models.user import User
from app.schemas.activity import ActivityCreate, ActivityUpdate, ActivityResponse
from app.services import activities as activity_service

router = APIRouter()


@router.post(
    "",
    response_model=ActivityResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Activity",
    description="Creates a new Activity (task, call, meeting, note, follow_up) within the user's organization."
)
async def create_activity(
    payload: ActivityCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> ActivityResponse:
    """Creates a new activity record."""
    return await activity_service.create_activity(db, current_user.organization_id, current_user.id, payload)


@router.get(
    "",
    response_model=List[ActivityResponse],
    status_code=status.HTTP_200_OK,
    summary="List Activities",
    description="Retrieves activities belonging exclusively to the authenticated user's organization."
)
async def list_activities(
    skip: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(100, ge=1, le=500, description="Pagination page limit"),
    customer_id: Optional[uuid.UUID] = Query(None, description="Filter by Customer UUID"),
    contact_id: Optional[uuid.UUID] = Query(None, description="Filter by Contact UUID"),
    deal_id: Optional[uuid.UUID] = Query(None, description="Filter by Deal UUID"),
    quotation_id: Optional[uuid.UUID] = Query(None, description="Filter by Quotation UUID"),
    activity_type: Optional[str] = Query(None, description="Filter by activity_type ('task', 'call', 'meeting', 'note', 'follow_up')"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status ('pending', 'completed', 'cancelled')"),
    priority: Optional[str] = Query(None, description="Filter by priority ('low', 'medium', 'high', 'urgent')"),
    assigned_to_user_id: Optional[uuid.UUID] = Query(None, description="Filter by assigned user UUID"),
    overdue: Optional[bool] = Query(None, description="Filter pending activities that are past due_at"),
    upcoming: Optional[bool] = Query(None, description="Filter pending activities with future due_at"),
    search: Optional[str] = Query(None, min_length=1, description="Search filter in title or description"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> List[ActivityResponse]:
    """Lists activities for the current organization."""
    return await activity_service.list_activities(
        db,
        current_user.organization_id,
        skip=skip,
        limit=limit,
        customer_id=customer_id,
        contact_id=contact_id,
        deal_id=deal_id,
        quotation_id=quotation_id,
        activity_type=activity_type,
        status=status_filter,
        priority=priority,
        assigned_to_user_id=assigned_to_user_id,
        overdue=overdue,
        upcoming=upcoming,
        search=search
    )


@router.get(
    "/{activity_id}",
    response_model=ActivityResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Activity Details",
    description="Retrieves a specific activity by ID within the user's organization."
)
async def get_activity(
    activity_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> ActivityResponse:
    """Gets activity by ID."""
    return await activity_service.get_activity_by_id(db, current_user.organization_id, activity_id)


@router.put(
    "/{activity_id}",
    response_model=ActivityResponse,
    status_code=status.HTTP_200_OK,
    summary="Update Activity",
    description="Updates an activity record within the user's organization."
)
async def update_activity(
    activity_id: uuid.UUID,
    payload: ActivityUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> ActivityResponse:
    """Updates activity details."""
    return await activity_service.update_activity(db, current_user.organization_id, activity_id, payload)


@router.post(
    "/{activity_id}/complete",
    response_model=ActivityResponse,
    status_code=status.HTTP_200_OK,
    summary="Complete Activity",
    description="Marks a pending activity as completed and sets server-side completion timestamp."
)
async def complete_activity(
    activity_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> ActivityResponse:
    """Marks activity completed."""
    return await activity_service.complete_activity(db, current_user.organization_id, activity_id)


@router.post(
    "/{activity_id}/cancel",
    response_model=ActivityResponse,
    status_code=status.HTTP_200_OK,
    summary="Cancel Activity",
    description="Marks a pending activity as cancelled."
)
async def cancel_activity(
    activity_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> ActivityResponse:
    """Marks activity cancelled."""
    return await activity_service.cancel_activity(db, current_user.organization_id, activity_id)


@router.delete(
    "/{activity_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Activity",
    description="Deletes an activity record (requires Admin role privileges)."
)
async def delete_activity(
    activity_id: uuid.UUID,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
) -> None:
    """Deletes an activity record."""
    await activity_service.delete_activity(db, current_user.organization_id, activity_id)
