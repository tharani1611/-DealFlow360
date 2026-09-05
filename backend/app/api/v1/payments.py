import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.payments import PaymentCreateRequest, PaymentResponse
from app.services import payments as payment_service

router = APIRouter()


@router.post("", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
async def record_payment(
    payload: PaymentCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Records a payment against an invoice with Decimal balance verification."""
    return await payment_service.record_payment(db, current_user.organization_id, payload, current_user)


@router.get("/invoice/{invoice_id}", response_model=List[PaymentResponse])
async def list_payments_for_invoice(
    invoice_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Lists payments recorded for an invoice."""
    return await payment_service.list_payments_for_invoice(db, current_user.organization_id, invoice_id)


@router.get("/customer/{customer_id}", response_model=List[PaymentResponse])
async def list_payments_for_customer(
    customer_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Lists payments recorded for a customer."""
    return await payment_service.list_payments_for_customer(db, current_user.organization_id, customer_id)


@router.get("/{payment_id}", response_model=PaymentResponse)
async def get_payment(
    payment_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Gets details of a recorded payment."""
    return await payment_service.get_payment(db, current_user.organization_id, payment_id)
