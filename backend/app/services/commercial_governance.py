import uuid
from typing import Optional, List, Dict
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.schemas.commercial_governance import CommercialGovernanceSummaryResponse
from app.schemas.approval_engine import QuotationApprovalResponse
from app.services import quotations as quotation_service
from app.services import margins as margins_service
from app.services import discount_governance as governance_service
from app.services import discount_risk as risk_service
from app.services import approval_engine as approval_service

logger = logging.getLogger("dealflow360.commercial_governance_orchestrator")


async def evaluate_commercial_governance(
    db: AsyncSession,
    organization_id: uuid.UUID,
    quotation_id: uuid.UUID,
    current_user_id: Optional[uuid.UUID] = None,
    user_role: Optional[str] = None
) -> CommercialGovernanceSummaryResponse:
    """
    Orchestrates the full commercial governance pipeline:
    Phase 20 Pricing -> Phase 21 Margin -> Phase 23 Governance -> Phase 24 Risk -> Phase 25 Approval.
    """
    # 1. Fetch quotation
    quotation = await quotation_service.get_quotation_by_id(db, organization_id, quotation_id)

    # 2. Phase 21 Margin Calculation
    margin_res = await margins_service.get_quotation_margin(db, organization_id, quotation_id)

    # 3. Phase 23 Discount Governance Evaluation
    gov_res = await governance_service.evaluate_discount_governance(
        db, organization_id, quotation_id=quotation_id, customer_id=quotation.customer_id, user_id=current_user_id, user_role=user_role
    )

    # 4. Phase 24 Blended Discount Risk Engine Evaluation
    risk_res = await risk_service.evaluate_discount_risk(
        db, organization_id, quotation_id=quotation_id, governance_res=gov_res, margin_res=margin_res
    )

    # 5. Phase 25 Approval Rule Engine Evaluation
    req_user = current_user_id or quotation.created_by_user_id or uuid.uuid4()
    approval_rec = await approval_service.evaluate_approval_requirement(
        db, organization_id, quotation_id=quotation_id, requested_by_user_id=req_user, governance_res=gov_res, risk_res=risk_res, margin_res=margin_res
    )

    req_name = None
    if approval_rec.requested_by_user:
        req_name = approval_rec.requested_by_user.full_name or approval_rec.requested_by_user.email

    appr_name = None
    if approval_rec.approved_by_user:
        appr_name = approval_rec.approved_by_user.full_name or approval_rec.approved_by_user.email

    approval_res = QuotationApprovalResponse(
        id=approval_rec.id,
        organization_id=approval_rec.organization_id,
        quotation_id=approval_rec.quotation_id,
        approval_rule_id=approval_rec.approval_rule_id,
        requested_by_user_id=approval_rec.requested_by_user_id,
        requested_by_user_name=req_name,
        approved_by_user_id=approval_rec.approved_by_user_id,
        approved_by_user_name=appr_name,
        status=approval_rec.status,
        approval_level=approval_rec.approval_level,
        reasons=approval_rec.reasons,
        decision_note=approval_rec.decision_note,
        created_at=approval_rec.created_at,
        updated_at=approval_rec.updated_at
    )

    return CommercialGovernanceSummaryResponse(
        quotation_id=quotation.id,
        quotation_number=quotation.quotation_number,
        customer_id=quotation.customer_id,
        currency=quotation.currency,
        total_amount=str(quotation.total_amount),
        margin=margin_res,
        governance=gov_res,
        risk=risk_res,
        approval=approval_res
    )
