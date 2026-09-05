import uuid
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.margin import MarginCalculateRequest, QuotationMarginResponse
from app.services import margins as margin_service

router = APIRouter()


@router.post(
    "/calculate",
    response_model=QuotationMarginResponse,
    status_code=status.HTTP_200_OK,
    summary="Calculate Real-time Margin Preview",
    description="Evaluates Phase 20 final selling prices, line costs, gross margins, margin percentages, and health classifications for single or multi-item quotation previews."
)
async def calculate_margin(
    payload: MarginCalculateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> QuotationMarginResponse:
    """Calculates live margin preview for line items."""
    return await margin_service.calculate_margin_preview(db, current_user.organization_id, payload)


@router.get(
    "/quotations/{quotation_id}",
    response_model=QuotationMarginResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Quotation Margin Breakdown",
    description="Retrieves historical line-level and aggregate quotation profitability breakdown using snapshotted unit prices and unit costs."
)
async def get_quotation_margin(
    quotation_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> QuotationMarginResponse:
    """Gets margin breakdown for an existing quotation."""
    return await margin_service.get_quotation_margin(db, current_user.organization_id, quotation_id)


@router.get(
    "/deals/{deal_id}",
    response_model=QuotationMarginResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Deal Margin Breakdown",
    description="Retrieves quotation margin breakdown for a deal's associated quotation."
)
async def get_deal_margin(
    deal_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> QuotationMarginResponse:
    """Gets margin breakdown for a deal's associated quotation."""
    return await margin_service.get_deal_margin(db, current_user.organization_id, deal_id)
