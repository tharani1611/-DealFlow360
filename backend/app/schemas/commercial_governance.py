import uuid
from typing import Optional
from pydantic import BaseModel, ConfigDict
from app.schemas.margin import QuotationMarginResponse
from app.schemas.discount_governance import GovernanceEvaluationResult
from app.schemas.discount_risk import RiskEvaluationResult
from app.schemas.approval_engine import QuotationApprovalResponse


class CommercialGovernanceSummaryResponse(BaseModel):
    """Integrated Commercial Governance Summary Response combining Pricing, Margin, Governance, Risk, and Approval."""
    quotation_id: Optional[uuid.UUID] = None
    quotation_number: Optional[str] = None
    customer_id: Optional[uuid.UUID] = None
    currency: str = "USD"
    total_amount: str
    margin: QuotationMarginResponse
    governance: GovernanceEvaluationResult
    risk: RiskEvaluationResult
    approval: QuotationApprovalResponse

    model_config = ConfigDict(from_attributes=True)
