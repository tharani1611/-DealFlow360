import json
import uuid
import re
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.ai.service import ai_service
from app.ai import prompts
from app.schemas.copilot import (
    CopilotRequest,
    CopilotResponse,
    CopilotIntentEnum,
    CopilotEvidenceItem
)
from app.schemas.ai import AIMetadata
from app.services.sales_intelligence import sales_intelligence_service
from app.services import intelligence as intelligence_service
from app.services import commercial_governance as governance_service
from app.services import forecast as forecast_service


class AISalesCopilotService:
    """Phase 29 — AI Sales Copilot service managing intent routing, controlled context retrieval, hallucination controls, and source evidence generation."""

    @staticmethod
    def detect_intent(query: str) -> CopilotIntentEnum:
        """Determines query intent category using deterministic keyword/pattern matching."""
        q = query.lower()

        if any(w in q for w in ["approval", "approve", "rejected approval", "pending approval", "authorization"]):
            return CopilotIntentEnum.APPROVAL
        if any(w in q for w in ["discount", "high discount", "blended discount", "discount risk", "policy limit"]):
            return CopilotIntentEnum.DISCOUNT
        if any(w in q for w in ["margin", "cogs", "gross margin", "low margin", "profitability"]):
            return CopilotIntentEnum.MARGIN
        if any(w in q for w in ["price", "pricing", "unit price", "price rule"]):
            return CopilotIntentEnum.PRICING
        if any(w in q for w in ["quote", "quotation", "proposal", "draft quote", "sent quote"]):
            return CopilotIntentEnum.QUOTATION
        if any(w in q for w in ["customer", "client", "account", "going cold", "cooling", "briefing"]):
            return CopilotIntentEnum.CUSTOMER
        if any(w in q for w in ["deal", "opportunity", "at risk", "health score", "closing soon", "stalled"]):
            return CopilotIntentEnum.DEAL
        if any(w in q for w in ["activity", "activities", "overdue", "call", "meeting", "task", "follow up"]):
            return CopilotIntentEnum.ACTIVITY
        if any(w in q for w in ["pipeline", "forecast", "revenue", "win rate", "stage breakdown", "summary"]):
            return CopilotIntentEnum.PIPELINE

        return CopilotIntentEnum.GENERAL_SALES

    @staticmethod
    async def process_copilot_inquiry(
        db: AsyncSession,
        organization_id: uuid.UUID,
        payload: CopilotRequest
    ) -> CopilotResponse:
        """Executes full Copilot inquiry pipeline: intent routing -> context retrieval -> AI synthesis -> evidence compilation."""
        user_msg = payload.message.strip()
        intent = AISalesCopilotService.detect_intent(user_msg)

        context_facts: Dict[str, Any] = {}
        evidence: List[CopilotEvidenceItem] = []
        recommendations: List[str] = []
        ref_deal_ids: List[uuid.UUID] = []
        ref_cust_ids: List[uuid.UUID] = []
        ref_quote_ids: List[uuid.UUID] = []

        # Controlled context retrieval based on intent & scoped IDs
        if payload.deal_id:
            deal_facts = await sales_intelligence_service.build_deal_structured_facts(db, organization_id, payload.deal_id)
            context_facts["scoped_deal"] = deal_facts
            ref_deal_ids.append(payload.deal_id)

            if "deal" in deal_facts:
                d = deal_facts["deal"]
                evidence.append(CopilotEvidenceItem(
                    entity_type="deal",
                    entity_id=payload.deal_id,
                    label="Deal Health",
                    value=f"{d.get('health_status').upper()} ({d.get('health_score')}/100)",
                    detail=f"Value: ₹{d.get('value')}, Stage: {d.get('stage')}"
                ))

        elif payload.customer_id:
            cust_facts = await sales_intelligence_service.build_customer_structured_facts(db, organization_id, payload.customer_id)
            context_facts["scoped_customer"] = cust_facts
            ref_cust_ids.append(payload.customer_id)

            if "customer" in cust_facts:
                c = cust_facts["customer"]
                eng = cust_facts.get("engagement", {})
                evidence.append(CopilotEvidenceItem(
                    entity_type="customer",
                    entity_id=payload.customer_id,
                    label="Customer Engagement",
                    value=f"{eng.get('engagement_status', 'N/A').upper()} ({eng.get('engagement_score', 0)}/100)",
                    detail=f"Account: {c.get('name')}"
                ))

        # Retrieve pipeline facts for general or pipeline/governance inquiries
        pipeline_facts = await sales_intelligence_service.build_pipeline_structured_facts(db, organization_id)
        context_facts["pipeline_summary"] = pipeline_facts

        dash_intel = pipeline_facts.get("dashboard_intelligence", {})
        pipe_metrics = dash_intel.get("pipeline", {})
        att_items = pipeline_facts.get("attention_center", {}).get("items", [])

        # Build evidence items from telemetry
        if intent == CopilotIntentEnum.PIPELINE:
            evidence.append(CopilotEvidenceItem(
                entity_type="pipeline",
                label="Open Pipeline Value",
                value=f"₹{pipe_metrics.get('open_pipeline_value', '0.00')}",
                detail=f"Weighted: ₹{pipe_metrics.get('weighted_pipeline_value', '0.00')}"
            ))
            evidence.append(CopilotEvidenceItem(
                entity_type="pipeline",
                label="Win Rate",
                value=str(pipe_metrics.get("win_rate", "0%")),
                detail="Historical conversion"
            ))

        elif intent in (CopilotIntentEnum.APPROVAL, CopilotIntentEnum.DISCOUNT, CopilotIntentEnum.MARGIN):
            deals_at_risk = dash_intel.get("deals_at_risk", [])
            for dr in deals_at_risk:
                evidence.append(CopilotEvidenceItem(
                    entity_type="deal",
                    entity_id=uuid.UUID(dr["deal_id"]) if "deal_id" in dr else None,
                    label="Commercial Risk Deal",
                    value=f"{dr.get('title')} ({dr.get('health_status')})",
                    detail=f"Risk Level: {dr.get('risk_level')}"
                ))
                if "deal_id" in dr:
                    ref_deal_ids.append(uuid.UUID(dr["deal_id"]))

        # Populate top attention recommendations
        for item in att_items[:3]:
            recommendations.append(f"{item.get('title')}: {item.get('description')}")
            if item.get("entity_type") == "deal" and "entity_id" in item:
                ref_deal_ids.append(uuid.UUID(item["entity_id"]))
            elif item.get("entity_type") == "customer" and "entity_id" in item:
                ref_cust_ids.append(uuid.UUID(item["entity_id"]))

        # De-duplicate referenced IDs
        ref_deal_ids = list(set(ref_deal_ids))
        ref_cust_ids = list(set(ref_cust_ids))

        # AI Prompt Synthesis
        provider = ai_service.get_provider()
        metadata = ai_service._get_metadata(provider)

        system_instruction = (
            "You are DealFlow360 AI Sales Copilot.\n"
            "Respond to the sales representative question using ONLY the provided structured DealFlow360 CRM context.\n"
            "CRITICAL CONSTRAINTS:\n"
            "1. Do NOT invent numbers, deals, customers, or financial calculations.\n"
            "2. Do NOT execute any database operations or claim actions were taken.\n"
            "3. Ground all statements in the supplied structured facts.\n"
            "4. If context is insufficient, state so clearly.\n"
            "5. Provide concise, high-value sales recommendations."
        )

        user_prompt = f"USER QUESTION ({intent.value}): {user_msg}\n\n" + prompts.wrap_untrusted_context(json.dumps(context_facts, indent=2))

        try:
            answer_text = await provider.generate_content(system_instruction, user_prompt)
            clean_answer = answer_text.strip() if answer_text else "No insights could be derived."
        except Exception as exc:
            # Fallback if AI provider is unavailable
            clean_answer = (
                f"Sales Copilot evaluated query under intent '{intent.value}'. "
                f"Current Open Pipeline stands at ₹{pipe_metrics.get('open_pipeline_value', '0.00')} "
                f"with {dash_intel.get('needs_attention_count', 0)} items requiring immediate attention. "
                "AI narrative explanation is temporarily offline."
            )

        return CopilotResponse(
            answer=clean_answer,
            intent=intent,
            evidence=evidence,
            recommendations=recommendations,
            referenced_deal_ids=ref_deal_ids[:5],
            referenced_customer_ids=ref_cust_ids[:5],
            referenced_quotation_ids=ref_quote_ids[:5],
            metadata=metadata
        )


ai_sales_copilot_service = AISalesCopilotService()
