import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.subscriptions import (
    SubscriptionCreateRequest,
    SubscriptionResponse,
    SubscriptionProrationRequest,
    SubscriptionProrationResponse,
    SubscriptionCancellationRequest,
    SubscriptionCancellationResponse,
    BillingScheduleResponse,
)
from app.schemas.invoices import InvoiceResponse
from app.services import subscriptions as subscription_service
from app.services import billing_schedules as schedule_service
from app.services import prorations as proration_service
from app.services import cancellations as cancellation_service

router = APIRouter()


@router.post("", response_model=SubscriptionResponse, status_code=status.HTTP_201_CREATED)
async def create_subscription(
    payload: SubscriptionCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Creates a new recurring subscription."""
    return await subscription_service.create_subscription(db, current_user.organization_id, payload)


@router.post("/quotation/{quotation_id}", response_model=List[SubscriptionResponse], status_code=status.HTTP_201_CREATED)
async def create_subscriptions_from_quotation(
    quotation_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generates subscriptions from recurring items of an accepted/converted quotation."""
    return await subscription_service.create_subscriptions_from_quotation(db, current_user.organization_id, quotation_id)


@router.get("", response_model=List[SubscriptionResponse])
async def list_subscriptions(
    customer_id: Optional[uuid.UUID] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Lists active/managed subscriptions for the user's organization."""
    return await subscription_service.list_subscriptions(db, current_user.organization_id, customer_id)


@router.get("/{subscription_id}", response_model=SubscriptionResponse)
async def get_subscription(
    subscription_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Gets details for a specific subscription."""
    return await subscription_service.get_subscription(db, current_user.organization_id, subscription_id)


@router.post("/{subscription_id}/status", response_model=SubscriptionResponse)
async def update_subscription_status(
    subscription_id: uuid.UUID,
    new_status: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Updates subscription status (TRIAL, ACTIVE, PAUSED, EXPIRED)."""
    return await subscription_service.update_subscription_status(db, current_user.organization_id, subscription_id, new_status)


@router.get("/{subscription_id}/schedules", response_model=List[BillingScheduleResponse])
async def list_schedules_for_subscription(
    subscription_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Lists billing schedules for a subscription."""
    return await schedule_service.list_schedules_for_subscription(db, current_user.organization_id, subscription_id)


@router.post("/schedules/generate-due", response_model=List[BillingScheduleResponse])
async def generate_due_schedules(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Triggers generation of due billing schedules for active subscriptions."""
    return await schedule_service.generate_due_billing_schedules(db, current_user.organization_id)


@router.post("/schedules/{schedule_id}/execute-invoice", response_model=InvoiceResponse)
async def execute_schedule_invoice(
    schedule_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generates an invoice for a due billing schedule entry with idempotency key check."""
    return await schedule_service.execute_billing_schedule_invoice(db, current_user.organization_id, schedule_id)


@router.post("/{subscription_id}/prorate", response_model=SubscriptionProrationResponse)
async def prorate_subscription(
    subscription_id: uuid.UUID,
    payload: SubscriptionProrationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Calculates Decimal day-count fraction proration adjustment for subscription changes."""
    return await proration_service.prorate_subscription_adjustment(db, current_user.organization_id, subscription_id, payload, current_user)


@router.get("/{subscription_id}/prorations", response_model=List[SubscriptionProrationResponse])
async def list_prorations_for_subscription(
    subscription_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Lists proration adjustment logs for a subscription."""
    return await proration_service.list_prorations_for_subscription(db, current_user.organization_id, subscription_id)


@router.post("/{subscription_id}/cancel", response_model=SubscriptionCancellationResponse)
async def cancel_subscription(
    subscription_id: uuid.UUID,
    payload: SubscriptionCancellationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Cancels a subscription (IMMEDIATE or END_OF_PERIOD)."""
    return await cancellation_service.cancel_subscription(db, current_user.organization_id, subscription_id, payload, current_user)
