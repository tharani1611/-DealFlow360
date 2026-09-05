import json
import uuid
from typing import Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import status

from app.core.config import settings
from app.core.exceptions import DealFlowException
from app.ai.base import AbstractAIProvider
from app.ai.providers.gemini import GeminiAIProvider
from app.ai.providers.mock import MockAIProvider
from app.ai.context import AIContextBuilder
from app.ai import prompts
from app.schemas.ai import (
    CustomerSummaryResponse,
    DealAnalysisResponse,
    NextActionResponse,
    ActivityInsightResponse,
    AssistantResponse,
    AIMetadata
)
from app.schemas.intelligence import SalesBriefingResponse


class AIService:
    """High-level AI Intelligence service orchestrating context building, prompt defense, and provider responses."""

    def __init__(self, provider: Optional[AbstractAIProvider] = None):
        self._provider_override = provider

    def get_provider(self) -> AbstractAIProvider:
        """Returns configured AI provider instance or mock override."""
        if not settings.AI_ENABLED:
            raise DealFlowException(
                message="AI Intelligence features are currently disabled on the server.",
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE
            )

        if self._provider_override:
            return self._provider_override

        provider_name = (settings.AI_PROVIDER or "gemini").lower()
        if provider_name == "mock":
            return MockAIProvider()
        return GeminiAIProvider()

    def _get_metadata(self, provider: AbstractAIProvider) -> AIMetadata:
        """Helper to derive AIMetadata block based on current active provider instance."""
        if isinstance(provider, MockAIProvider):
            return AIMetadata(provider="mock", model=getattr(provider, "model", "mock-model"))
        p_name = (settings.AI_PROVIDER or "gemini").lower()
        m_name = getattr(provider, "model", settings.GEMINI_MODEL)
        return AIMetadata(provider=p_name, model=m_name)

    async def summarize_customer(
        self,
        db: AsyncSession,
        organization_id: uuid.UUID,
        customer_id: uuid.UUID
    ) -> CustomerSummaryResponse:
        """Generates structured CRM relationship summary for a customer."""
        provider = self.get_provider()
        context_data = await AIContextBuilder.build_customer_context(db, organization_id, customer_id)
        user_prompt = prompts.wrap_untrusted_context(json.dumps(context_data, indent=2))

        schema = {
            "type": "object",
            "properties": {
                "summary": {"type": "string"},
                "key_insights": {"type": "array", "items": {"type": "string"}},
                "health_score_estimate": {"type": "string", "enum": ["good", "neutral", "at_risk"]}
            },
            "required": ["summary", "key_insights", "health_score_estimate"]
        }

        output = await provider.generate_structured(prompts.CUSTOMER_SUMMARY_SYSTEM_PROMPT, user_prompt, schema)

        return CustomerSummaryResponse(
            customer_id=customer_id,
            customer_name=context_data["customer"]["name"],
            summary=output.get("summary", "Customer summary generated."),
            key_insights=output.get("key_insights", []),
            health_score_estimate=output.get("health_score_estimate", "good"),
            metadata=self._get_metadata(provider)
        )

    async def analyze_deal(
        self,
        db: AsyncSession,
        organization_id: uuid.UUID,
        deal_id: uuid.UUID
    ) -> DealAnalysisResponse:
        """Generates structured risk and opportunity analysis for a deal."""
        provider = self.get_provider()
        context_data = await AIContextBuilder.build_deal_context(db, organization_id, deal_id)
        user_prompt = prompts.wrap_untrusted_context(json.dumps(context_data, indent=2))

        schema = {
            "type": "object",
            "properties": {
                "summary": {"type": "string"},
                "risk_level": {"type": "string", "enum": ["low", "medium", "high"]},
                "risks": {"type": "array", "items": {"type": "string"}},
                "positive_signals": {"type": "array", "items": {"type": "string"}},
                "recommended_actions": {"type": "array", "items": {"type": "string"}}
            },
            "required": ["summary", "risk_level", "risks", "positive_signals", "recommended_actions"]
        }

        output = await provider.generate_structured(prompts.DEAL_ANALYSIS_SYSTEM_PROMPT, user_prompt, schema)

        return DealAnalysisResponse(
            deal_id=deal_id,
            deal_number=context_data["deal"]["deal_number"],
            summary=output.get("summary", "Deal analysis completed."),
            risk_level=output.get("risk_level", "medium"),
            risks=output.get("risks", []),
            positive_signals=output.get("positive_signals", []),
            recommended_actions=output.get("recommended_actions", []),
            metadata=self._get_metadata(provider)
        )

    async def recommend_next_action(
        self,
        db: AsyncSession,
        organization_id: uuid.UUID,
        deal_id: uuid.UUID
    ) -> NextActionResponse:
        """Recommends next best CRM action for a deal."""
        provider = self.get_provider()
        context_data = await AIContextBuilder.build_deal_context(db, organization_id, deal_id)
        user_prompt = prompts.wrap_untrusted_context(json.dumps(context_data, indent=2))

        schema = {
            "type": "object",
            "properties": {
                "action_type": {"type": "string", "enum": ["task", "call", "meeting", "follow_up"]},
                "title": {"type": "string"},
                "reason": {"type": "string"},
                "priority": {"type": "string", "enum": ["low", "medium", "high", "urgent"]}
            },
            "required": ["action_type", "title", "reason", "priority"]
        }

        output = await provider.generate_structured(prompts.NEXT_ACTION_SYSTEM_PROMPT, user_prompt, schema)

        return NextActionResponse(
            deal_id=deal_id,
            action_type=output.get("action_type", "follow_up"),
            title=output.get("title", "Follow up with customer"),
            reason=output.get("reason", "Recommended based on recent activity history."),
            priority=output.get("priority", "medium"),
            metadata=self._get_metadata(provider)
        )

    async def analyze_deal_activities(
        self,
        db: AsyncSession,
        organization_id: uuid.UUID,
        deal_id: uuid.UUID
    ) -> ActivityInsightResponse:
        """Analyzes deal activity engagement velocity and overdue items."""
        provider = self.get_provider()
        context_data = await AIContextBuilder.build_deal_context(db, organization_id, deal_id)
        user_prompt = prompts.wrap_untrusted_context(json.dumps(context_data, indent=2))

        schema = {
            "type": "object",
            "properties": {
                "summary": {"type": "string"},
                "insights": {"type": "array", "items": {"type": "string"}},
                "recommended_follow_ups": {"type": "array", "items": {"type": "string"}}
            },
            "required": ["summary", "insights", "recommended_follow_ups"]
        }

        output = await provider.generate_structured(prompts.ACTIVITY_INSIGHTS_SYSTEM_PROMPT, user_prompt, schema)

        acts = context_data.get("activities", [])
        overdue_cnt = sum(1 for a in acts if a.get("status") == "pending" and a.get("due_at"))
        upcoming_cnt = sum(1 for a in acts if a.get("status") == "pending")

        return ActivityInsightResponse(
            deal_id=deal_id,
            summary=output.get("summary", "Activity analysis completed."),
            overdue_count=overdue_cnt,
            upcoming_count=upcoming_cnt,
            insights=output.get("insights", []),
            recommended_follow_ups=output.get("recommended_follow_ups", []),
            metadata=self._get_metadata(provider)
        )

    async def answer_assistant_question(
        self,
        db: AsyncSession,
        organization_id: uuid.UUID,
        question: str
    ) -> AssistantResponse:
        """Answers general user question using tenant-isolated CRM context."""
        provider = self.get_provider()
        context_data = await AIContextBuilder.build_assistant_context(db, organization_id)
        
        user_prompt = f"USER QUESTION: {question}\n\n" + prompts.wrap_untrusted_context(json.dumps(context_data, indent=2))

        answer = await provider.generate_content(prompts.CRM_ASSISTANT_SYSTEM_PROMPT, user_prompt)
        referenced_ids = [uuid.UUID(d["id"]) for d in context_data.get("deals", []) if "id" in d][:5]

        return AssistantResponse(
            answer=answer.strip() if answer else "No additional insights available.",
            context_used_count=len(context_data.get("deals", [])) + len(context_data.get("pending_activities", [])),
            referenced_deal_ids=referenced_ids,
            metadata=self._get_metadata(provider)
        )

    async def generate_sales_briefing(
        self,
        db: AsyncSession,
        organization_id: uuid.UUID,
        customer_id: uuid.UUID,
        deterministic_briefing: SalesBriefingResponse
    ) -> SalesBriefingResponse:
        """Synthesizes AI powered talking points, next actions, and pre-drafted follow-up email from deterministic customer facts."""
        try:
            provider = self.get_provider()
            context_data = await AIContextBuilder.build_customer_context(db, organization_id, customer_id)
            context_data["deterministic_briefing"] = deterministic_briefing.model_dump(mode="json")

            user_prompt = prompts.wrap_untrusted_context(json.dumps(context_data, indent=2))

            schema = {
                "type": "object",
                "properties": {
                    "talking_points": {"type": "array", "items": {"type": "string"}},
                    "suggested_next_actions": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "title": {"type": "string"},
                                "action_type": {"type": "string"},
                                "priority": {"type": "string"}
                            }
                        }
                    },
                    "suggested_followup_message": {"type": "string"}
                },
                "required": ["talking_points", "suggested_next_actions", "suggested_followup_message"]
            }

            output = await provider.generate_structured(prompts.SALES_BRIEFING_SYSTEM_PROMPT, user_prompt, schema)

            deterministic_briefing.talking_points = output.get("talking_points", deterministic_briefing.talking_points)
            deterministic_briefing.suggested_next_actions = output.get("suggested_next_actions", deterministic_briefing.suggested_next_actions)
            deterministic_briefing.suggested_followup_message = output.get("suggested_followup_message", deterministic_briefing.suggested_followup_message)
            deterministic_briefing.metadata = self._get_metadata(provider)
        except Exception:
            # Fallback gracefully if AI service disabled or errors out
            pass

        return deterministic_briefing

    async def explain_deal_health(
        self,
        db: AsyncSession,
        organization_id: uuid.UUID,
        deal_id: uuid.UUID,
        health_resp: Any
    ) -> str:
        """Generates concise AI explanation for calculated deal health score and risks."""
        try:
            provider = self.get_provider()
            context_data = {
                "health_score": health_resp.health_score,
                "health_status": health_resp.health_status,
                "risk_level": health_resp.risk_level,
                "risk_factors": [rf.model_dump(mode="json") for rf in health_resp.risk_factors],
                "metrics": health_resp.metrics.model_dump(mode="json")
            }
            user_prompt = prompts.wrap_untrusted_context(json.dumps(context_data, indent=2))
            explanation = await provider.generate_content(prompts.HEALTH_EXPLANATION_SYSTEM_PROMPT, user_prompt)
            if explanation:
                return explanation.strip()
        except Exception:
            pass

        # Fallback explanation
        if health_resp.health_score >= 80:
            return "Deal exhibits strong momentum, high probability, and active engagement with no major risks."
        elif health_resp.health_score >= 60:
            return "Deal status is stable with normal pipeline progress."
        elif health_resp.health_score >= 40:
            return "Deal health is at risk due to overdue activities or inactive engagement."
        return "Deal is in critical condition requiring immediate sales intervention."

    async def explain_revenue_forecast(
        self,
        db: AsyncSession,
        organization_id: uuid.UUID,
        forecast_resp: Any
    ) -> str:
        """Generates concise AI executive commentary for calculated revenue forecast."""
        try:
            provider = self.get_provider()
            context_data = {
                "open_pipeline": forecast_resp.open_pipeline,
                "forecast_revenue": forecast_resp.forecast_revenue,
                "committed_revenue": forecast_resp.committed_revenue,
                "upside_revenue": forecast_resp.upside_revenue,
                "at_risk_revenue": forecast_resp.at_risk_revenue,
                "confidence_score": forecast_resp.confidence_score,
                "confidence_label": forecast_resp.confidence_label,
                "concentration_risk": forecast_resp.concentration_risk,
                "positive_factors": forecast_resp.confidence_factors.positive_factors,
                "negative_factors": forecast_resp.confidence_factors.negative_factors,
            }
            user_prompt = prompts.wrap_untrusted_context(json.dumps(context_data, indent=2))
            explanation = await provider.generate_content(prompts.FORECAST_EXPLANATION_SYSTEM_PROMPT, user_prompt)
            if explanation:
                return explanation.strip()
        except Exception:
            pass

        return f"Revenue forecast of ${forecast_resp.forecast_revenue} evaluated with {forecast_resp.confidence_label} ({forecast_resp.confidence_score}/100). Committed pipeline stands at ${forecast_resp.committed_revenue} with ${forecast_resp.at_risk_revenue} identified as at risk."

    async def explain_customer_health(
        self,
        db: AsyncSession,
        organization_id: uuid.UUID,
        cust_360: Any
    ) -> str:
        """Generates concise AI executive commentary explaining customer health score and driver factors."""
        try:
            provider = self.get_provider()
            context_data = {
                "customer_name": cust_360.customer_name,
                "health_score": cust_360.health.health_score,
                "health_category": cust_360.health.health_category,
                "segment": cust_360.health.segment,
                "lifecycle_stage": cust_360.health.lifecycle_stage,
                "positive_drivers": cust_360.health.positive_drivers,
                "negative_drivers": cust_360.health.negative_drivers,
                "won_revenue": cust_360.financials.total_won_revenue,
                "open_pipeline": cust_360.financials.open_pipeline
            }
            user_prompt = prompts.wrap_untrusted_context(json.dumps(context_data, indent=2))
            explanation = await provider.generate_content(prompts.CUSTOMER_HEALTH_EXPLANATION_SYSTEM_PROMPT, user_prompt)
            if explanation:
                return explanation.strip()
        except Exception:
            pass

        return f"Account '{cust_360.customer_name}' evaluates to health score {cust_360.health.health_score}/100 ({cust_360.health.health_category}). Segmented as {cust_360.health.segment} with won revenue of ${cust_360.financials.total_won_revenue} and open pipeline of ${cust_360.financials.open_pipeline}."

    async def explain_product_performance(
        self,
        db: AsyncSession,
        organization_id: uuid.UUID,
        prod_360: Any
    ) -> str:
        """Generates concise AI advisory explanation for product sales performance and margins."""
        try:
            provider = self.get_provider()
            context_data = {
                "product_name": prod_360.name,
                "sku": prod_360.sku,
                "total_revenue": prod_360.performance.total_revenue,
                "gross_margin": prod_360.performance.gross_margin,
                "margin_percentage": prod_360.performance.margin_percentage,
                "units_won": prod_360.performance.units_won,
                "penetration_rate_percent": prod_360.performance.penetration_rate_percent,
                "popularity_rank": prod_360.performance.popularity_rank,
                "affinities": [aff.model_dump(mode="json") for aff in prod_360.affinities]
            }
            user_prompt = prompts.wrap_untrusted_context(json.dumps(context_data, indent=2))
            explanation = await provider.generate_content(prompts.PRODUCT_PERFORMANCE_EXPLANATION_SYSTEM_PROMPT, user_prompt)
            if explanation:
                return explanation.strip()
        except Exception:
            pass

        return f"Product '{prod_360.name}' generated ${prod_360.performance.total_revenue} in total revenue with a gross margin of {prod_360.performance.margin_percentage}% across {prod_360.performance.units_won} units sold, achieving a {prod_360.performance.penetration_rate_percent}% customer penetration rate."


ai_service = AIService()

