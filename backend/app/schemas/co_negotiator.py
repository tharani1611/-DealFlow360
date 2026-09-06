from uuid import UUID
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field


class NegotiationSimulationRequest(BaseModel):
    requested_discount_percent: Optional[Decimal] = Field(None, ge=Decimal("0.00"), le=Decimal("100.00"))
    target_win_probability: Optional[int] = Field(80, ge=1, le=100)
    customer_notes: Optional[str] = None


class SimulationScenario(BaseModel):
    scenario_id: str
    title: str
    strategy_type: str  # BALANCED, VOLUME_INCENTIVE, VALUE_ADD_SWAP
    recommended_discount_percent: Decimal
    recommended_volume_commitment: int
    offered_perks: List[str]
    simulated_win_probability: int
    projected_gross_revenue: Decimal
    projected_gross_margin_percent: Decimal
    projected_net_profit: Decimal
    risk_assessment: str  # LOW_RISK, MODERATE_RISK, HIGH_MARGIN_EROSION
    reasoning_summary: str
    counter_proposal_script: str
    model_config = ConfigDict(from_attributes=True)


class NegotiationSimulationResponse(BaseModel):
    quotation_id: UUID
    quotation_number: str
    original_total: Decimal
    original_margin_percent: Decimal
    simulated_scenarios_count: int = 120
    recommended_scenarios: List[SimulationScenario]
    model_config = ConfigDict(from_attributes=True)
