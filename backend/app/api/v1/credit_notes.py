import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.credit_notes import (
    CreditNoteCreateRequest,
    CreditNoteResponse,
    PaymentRefundCreateRequest,
    PaymentRefundResponse,
)
from app.services import credit_notes as credit_note_service

router = APIRouter()


@router.post("", response_model=CreditNoteResponse, status_code=status.HTTP_201_CREATED)
async def create_credit_note(
    payload: CreditNoteCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Creates an issued credit note against an invoice, deducting receivable amount due."""
    return await credit_note_service.create_credit_note(db, current_user.organization_id, payload, current_user)


@router.get("/{credit_note_id}", response_model=CreditNoteResponse)
async def get_credit_note(
    credit_note_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Gets credit note details."""
    return await credit_note_service.get_credit_note(db, current_user.organization_id, credit_note_id)


@router.get("/invoice/{invoice_id}", response_model=List[CreditNoteResponse])
async def list_credit_notes_for_invoice(
    invoice_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Lists credit notes issued for an invoice."""
    return await credit_note_service.list_credit_notes_for_invoice(db, current_user.organization_id, invoice_id)


@router.post("/refunds", response_model=PaymentRefundResponse, status_code=status.HTTP_201_CREATED)
async def record_payment_refund(
    payload: PaymentRefundCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Records a cash payment refund with maximum refund validation."""
    return await credit_note_service.record_payment_refund(db, current_user.organization_id, payload, current_user)


@router.get("/refunds/payment/{payment_id}", response_model=List[PaymentRefundResponse])
async def list_refunds_for_payment(
    payment_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Lists payment refunds recorded for a payment."""
    return await credit_note_service.list_refunds_for_payment(db, current_user.organization_id, payment_id)
