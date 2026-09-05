import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.invoices import (
    InvoiceCreateRequest,
    InvoiceResponse,
)
from app.services import invoices as invoice_service

router = APIRouter()


@router.post("", response_model=InvoiceResponse, status_code=status.HTTP_201_CREATED)
async def create_invoice(
    payload: InvoiceCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Creates a new draft invoice with deterministic Decimal calculation."""
    return await invoice_service.create_invoice(db, current_user.organization_id, payload)


@router.post("/quotation/{quotation_id}", response_model=InvoiceResponse, status_code=status.HTTP_201_CREATED)
async def create_invoice_from_quotation(
    quotation_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generates an invoice from an accepted or converted quotation for physical one-time items."""
    return await invoice_service.create_invoice_from_quotation(db, current_user.organization_id, quotation_id)


@router.post("/{invoice_id}/issue", response_model=InvoiceResponse)
async def issue_invoice(
    invoice_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Transitions a DRAFT invoice to ISSUED."""
    return await invoice_service.issue_invoice(db, current_user.organization_id, invoice_id)


@router.post("/{invoice_id}/void", response_model=InvoiceResponse)
async def void_invoice(
    invoice_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Voids an un-paid invoice."""
    return await invoice_service.void_invoice(db, current_user.organization_id, invoice_id)


@router.get("", response_model=List[InvoiceResponse])
async def list_invoices(
    skip: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(100, ge=1, le=500, description="Pagination page limit"),
    customer_id: Optional[uuid.UUID] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Lists invoices for the user's organization."""
    return await invoice_service.list_invoices(
        db, current_user.organization_id, customer_id=customer_id, skip=skip, limit=limit
    )


@router.get("/{invoice_id}", response_model=InvoiceResponse)
async def get_invoice(
    invoice_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Gets details for a specific invoice with tenant isolation."""
    return await invoice_service.get_invoice(db, current_user.organization_id, invoice_id)
