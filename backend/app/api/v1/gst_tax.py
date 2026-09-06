import uuid
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.core.exceptions import NotFoundException
from app.models.invoice import Invoice
from app.models.organization import Organization
from app.models.customer import Customer
from app.schemas.gst import (
    GSTTaxCalculationRequest,
    GSTTaxCalculationResponse,
    EWayBillPayloadRequest,
)
from app.services.gst_engine import calculate_gst_breakdown
from app.services.einvoice_engine import build_einvoice_irn_payload, build_eway_bill_payload

router = APIRouter()


@router.post("/gst/calculate-tax", response_model=GSTTaxCalculationResponse)
async def calculate_gst_tax_endpoint(
    payload: GSTTaxCalculationRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Computes GST tax breakdown (Intra-state CGST+SGST vs Inter-state IGST) based on seller & buyer state.
    """
    line_items_data = [item.model_dump() for item in payload.items]
    res = calculate_gst_breakdown(
        seller_state=payload.seller_state,
        buyer_state=payload.buyer_state,
        line_items=line_items_data,
    )
    return res


@router.get("/invoices/{invoice_id}/einvoice-payload")
async def get_einvoice_irn_payload(
    invoice_id: uuid.UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Generates official NIC B2B E-Invoicing IRN JSON payload schema for government portal dispatch.
    """
    org_id = current_user.organization_id

    # Fetch Invoice
    inv_stmt = select(Invoice).where(Invoice.id == invoice_id, Invoice.organization_id == org_id)
    inv_res = await session.execute(inv_stmt)
    invoice = inv_res.scalar_one_or_none()
    if not invoice:
        raise NotFoundException(f"Invoice {invoice_id} not found")

    # Fetch Org & Customer
    org = await session.get(Organization, org_id)
    customer = await session.get(Customer, invoice.customer_id)

    payload = build_einvoice_irn_payload(
        invoice=invoice,
        organization=org,
        customer=customer,
        items=invoice.items or [],
        seller_state="Karnataka",
    )
    return payload


@router.post("/invoices/{invoice_id}/ewaybill-payload")
async def get_eway_bill_payload(
    invoice_id: uuid.UUID,
    body: EWayBillPayloadRequest,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Generates official NIC E-Way Bill JSON payload schema for transport logistics dispatch.
    """
    org_id = current_user.organization_id

    # Fetch Invoice
    inv_stmt = select(Invoice).where(Invoice.id == invoice_id, Invoice.organization_id == org_id)
    inv_res = await session.execute(inv_stmt)
    invoice = inv_res.scalar_one_or_none()
    if not invoice:
        raise NotFoundException(f"Invoice {invoice_id} not found")

    # Fetch Org & Customer
    org = await session.get(Organization, org_id)
    customer = await session.get(Customer, invoice.customer_id)

    payload = build_eway_bill_payload(
        invoice=invoice,
        organization=org,
        customer=customer,
        items=invoice.items or [],
        transporter_id=body.transporter_id,
        vehicle_no=body.vehicle_no,
        distance_km=body.distance_km,
        seller_state=body.seller_state or "Karnataka",
    )
    return payload
