import json
import uuid
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import status

from app.core.exceptions import NotFoundException
from app.ai.service import ai_service
from app.ai.base import AbstractAIProvider
from app.ai import prompts
from app.schemas.copilot import DealQAResponse
from app.schemas.ai import AIMetadata
from app.services.sales_intelligence import sales_intelligence_service


class DealIntelligenceService:
    """Phase 27 — Deal Intelligence service providing explainable deal metrics, health, risk factors, and Q&A."""

    @staticmethod
    async def get_deal_structured_facts(
        db: AsyncSession,
        organization_id: uuid.UUID,
        deal_id: uuid.UUID
    ) -> Dict[str, Any]:
        """Retrieves structured deal facts including commercial governance and health data."""
        facts = await sales_intelligence_service.build_deal_structured_facts(db, organization_id, deal_id)
        if "error" in facts:
            raise NotFoundException(facts["error"])
        return facts

    @staticmethod
    async def answer_deal_qa(
        db: AsyncSession,
        organization_id: uuid.UUID,
        deal_id: uuid.UUID,
        question: str
    ) -> DealQAResponse:
        """Answers natural language questions specific to a deal using retrieved structured context."""
        facts = await DealIntelligenceService.get_deal_structured_facts(db, organization_id, deal_id)

        deal_data = facts.get("deal", {})
        customer_data = facts.get("customer", {})
        quotation_data = facts.get("quotation")
        gov_data = facts.get("commercial_governance")

        key_facts = [
            f"Deal: {deal_data.get('title')} ({deal_data.get('deal_number')})",
            f"Value: ₹{deal_data.get('value')}, Stage: {deal_data.get('stage')}, Health: {deal_data.get('health_status').upper()} ({deal_data.get('health_score')}/100)",
        ]

        if quotation_data:
            key_facts.append(f"Quotation: {quotation_data.get('quotation_number')} (Status: {quotation_data.get('status').upper()}, Amount: ₹{quotation_data.get('total_amount')})")

        if gov_data:
            risk_info = gov_data.get("risk", {})
            app_info = gov_data.get("approval", {})
            key_facts.append(f"Commercial Risk: {risk_info.get('risk_level')} (Score: {risk_info.get('risk_score')}/100, Blended Disc: {risk_info.get('blended_discount_percent')}%)")
            key_facts.append(f"Approval Status: {app_info.get('approval_status')}")

        provider = ai_service.get_provider()
        metadata = ai_service._get_metadata(provider)

        # Build prompt
        system_instruction = (
            "You are DealFlow360 Deal Intelligence Assistant.\n"
            "Respond to the user question about this specific Deal using ONLY the provided structured DealFlow360 context.\n"
            "Never invent facts or calculate financial metrics outside the provided context.\n"
            "If information is unavailable, say so clearly.\n"
            "Instruct the user on recommended next sales actions."
        )

        context_json = json.dumps(facts, indent=2)
        user_prompt = f"DEAL QA QUESTION: {question}\n\n" + prompts.wrap_untrusted_context(context_json)

        try:
            answer = await provider.generate_content(system_instruction, user_prompt)
            clean_answer = answer.strip() if answer else "No additional deal intelligence available."
        except Exception as exc:
            # Fallback if AI provider is offline
            clean_answer = (
                f"Deal '{deal_data.get('title')}' is currently in stage '{deal_data.get('stage')}' "
                f"with health status '{deal_data.get('health_status')}' ({deal_data.get('health_score')}/100). "
                f"Quotation status is '{quotation_data.get('status') if quotation_data else 'None'}'. "
                "AI narrative explanation is temporarily offline."
            )

        recommended_action = (
            deal_data.get("risk_factors")[0].get("recommendation")
            if deal_data.get("risk_factors") and len(deal_data.get("risk_factors")) > 0
            else "Follow up with customer to advance deal stage."
        )

        return DealQAResponse(
            deal_id=deal_id,
            question=question,
            answer=clean_answer,
            key_facts=key_facts,
            recommended_action=recommended_action,
            metadata=metadata
        )


deal_intelligence_service = DealIntelligenceService()
