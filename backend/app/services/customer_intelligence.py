import json
import uuid
from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import status

from app.core.exceptions import NotFoundException
from app.ai.service import ai_service
from app.ai import prompts
from app.schemas.intelligence import SalesBriefingResponse, CustomerEngagementResponse
from app.services.sales_intelligence import sales_intelligence_service
from app.services import intelligence as intelligence_service


class CustomerIntelligenceService:
    """Phase 28 — Customer Intelligence (Customer 360) service providing relationship health, commercial observations, and meeting briefings."""

    @staticmethod
    async def get_customer_360_facts(
        db: AsyncSession,
        organization_id: uuid.UUID,
        customer_id: uuid.UUID
    ) -> Dict[str, Any]:
        """Retrieves complete Customer 360 facts across deals, quotations, engagement, and contacts."""
        facts = await sales_intelligence_service.build_customer_structured_facts(db, organization_id, customer_id)
        if "error" in facts:
            raise NotFoundException(facts["error"])
        return facts

    @staticmethod
    async def generate_customer_briefing(
        db: AsyncSession,
        organization_id: uuid.UUID,
        customer_id: uuid.UUID
    ) -> SalesBriefingResponse:
        """Generates executive Sales & Account Briefing for meeting preparation."""
        # Delegates to intelligence_service.get_sales_briefing which synthesizes deterministic data with AI
        return await intelligence_service.get_sales_briefing(db, organization_id, customer_id)

    @staticmethod
    async def get_customer_health(
        db: AsyncSession,
        organization_id: uuid.UUID,
        customer_id: uuid.UUID
    ) -> CustomerEngagementResponse:
        """Calculates deterministic customer engagement score and relationship health classification."""
        return await intelligence_service.calculate_customer_engagement(db, organization_id, customer_id)


customer_intelligence_service = CustomerIntelligenceService()
