import uuid
from datetime import date
from typing import List, Optional, Dict
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_user, require_admin
from app.models.user import User
from app.schemas.deal import DealCreate, DealUpdate, DealResponse, PipelineResponse
from app.schemas.activity import ActivityResponse
from app.services import deals as deal_service
from app.services import activities as activity_service

router = APIRouter()


@router.post(
    "",
    response_model=DealResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Deal",
    description="Creates a new Deal within the authenticated user's organization."
)
async def create_deal(
    payload: DealCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> DealResponse:
    """Creates a new deal record."""
    return await deal_service.create_deal(db, current_user.organization_id, payload)


@router.get(
    "/pipeline",
    response_model=PipelineResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Pipeline Deals (Kanban View)",
    description="Retrieves all organization deals grouped by pipeline stage for Kanban views."
)
async def get_deals_pipeline(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> PipelineResponse:
    """Gets deals grouped by pipeline stage."""
    stages_dict = await deal_service.get_deals_pipeline(db, current_user.organization_id)
    # Convert DB model items to DealResponse objects for response serialization
    formatted_stages = {
        st: [DealResponse.model_validate(d) for d in deals]
        for st, deals in stages_dict.items()
    }
    return PipelineResponse(stages=formatted_stages)


@router.get(
    "",
    response_model=List[DealResponse],
    status_code=status.HTTP_200_OK,
    summary="List Deals",
    description="Retrieves deals belonging exclusively to the authenticated user's organization."
)
async def list_deals(
    skip: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(100, ge=1, le=500, description="Pagination page limit"),
    stage: Optional[str] = Query(None, description="Stage filter ('new', 'qualified', 'proposal', 'negotiation', 'won', 'lost')"),
    status_filter: Optional[str] = Query(None, alias="status", description="Status filter ('open', 'won', 'lost')"),
    customer_id: Optional[uuid.UUID] = Query(None, description="Customer UUID filter"),
    search: Optional[str] = Query(None, min_length=1, description="Search filter in title or deal_number"),
    expected_close_date: Optional[date] = Query(None, description="Expected close date filter"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> List[DealResponse]:
    """Lists deals for the current organization."""
    return await deal_service.list_deals(
        db,
        current_user.organization_id,
        skip=skip,
        limit=limit,
        stage=stage,
        status=status_filter,
        customer_id=customer_id,
        search=search,
        expected_close_date=expected_close_date
    )


@router.get(
    "/{deal_id}",
    response_model=DealResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Deal Details",
    description="Retrieves a specific deal by ID within the authenticated user's organization."
)
async def get_deal(
    deal_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> DealResponse:
    """Gets deal by ID."""
    return await deal_service.get_deal_by_id(db, current_user.organization_id, deal_id)


@router.put(
    "/{deal_id}",
    response_model=DealResponse,
    status_code=status.HTTP_200_OK,
    summary="Update Deal",
    description="Updates a deal record within the authenticated user's organization."
)
async def update_deal(
    deal_id: uuid.UUID,
    payload: DealUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> DealResponse:
    """Updates deal details."""
    return await deal_service.update_deal(db, current_user.organization_id, deal_id, payload)


@router.delete(
    "/{deal_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Deal",
    description="Deletes a deal record (requires Admin role privileges)."
)
async def delete_deal(
    deal_id: uuid.UUID,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
) -> None:
    """Deletes a deal record."""
    await deal_service.delete_deal(db, current_user.organization_id, deal_id)


@router.get(
    "/{deal_id}/activities",
    response_model=List[ActivityResponse],
    status_code=status.HTTP_200_OK,
    summary="Get Deal Activity Timeline",
    description="Retrieves chronological activity timeline (newest first) for a specific deal."
)
async def get_deal_activities(
    deal_id: uuid.UUID,
    skip: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(100, ge=1, le=500, description="Pagination page limit"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> List[ActivityResponse]:
    """Gets deal activity timeline."""
    return await activity_service.get_deal_activities(
        db, current_user.organization_id, deal_id, skip=skip, limit=limit
    )
