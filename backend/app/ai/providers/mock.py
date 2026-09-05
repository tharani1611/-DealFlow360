import json
import logging
from typing import Dict, Any, Optional
from app.ai.base import AbstractAIProvider

logger = logging.getLogger("dealflow360.ai.mock")


class MockAIProvider(AbstractAIProvider):
    """Mock AI Provider for deterministic, offline test execution."""

    def __init__(self, model: str = "mock-model"):
        self.model = model

    async def generate_content(
        self,
        system_instruction: str,
        user_prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> str:
        """Returns deterministic mock text based on prompt keywords."""
        if "assistant" in system_instruction.lower() or "assistant" in user_prompt.lower():
            return "Based on your CRM data, 1 deal requires follow-up this week due to upcoming closing date."
        return "Mock AI Provider text response generated successfully."

    async def generate_structured(
        self,
        system_instruction: str,
        user_prompt: str,
        schema_dict: Dict[str, Any],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        """Returns mock JSON matching expected response schemas."""
        sys_lower = system_instruction.lower()

        schema_str = str(schema_dict)

        if "health_score_estimate" in schema_str or "customer" in sys_lower:
            return {
                "summary": "Customer has active account history with multiple open deals and quotations.",
                "key_insights": ["High engagement level", "Multiple active quotations"],
                "health_score_estimate": "good"
            }
        elif "risk_level" in schema_str or "positive_signals" in schema_str:
            return {
                "summary": "Deal is progressing normally through proposal stage with good quotation alignment.",
                "risk_level": "low",
                "risks": ["No recent activity logged in past 10 days"],
                "positive_signals": ["Customer requested proposal", "High win probability"],
                "recommended_actions": ["Schedule follow-up call with primary contact"]
            }
        elif "action_type" in schema_str:
            return {
                "action_type": "follow_up",
                "title": "Follow up on proposal feedback",
                "reason": "Quotation delivered 3 days ago; customer review pending.",
                "priority": "high"
            }
        elif "overdue_count" in schema_str or "recommended_follow_ups" in schema_str:
            return {
                "summary": "Deal activity momentum is steady with 1 upcoming follow-up scheduled.",
                "insights": ["Recent call completed successfully"],
                "recommended_follow_ups": ["Send formal meeting summary email"]
            }
        elif "talking_points" in schema_str:
            return {
                "talking_points": [
                    "Confirm technical requirements for enterprise rollout",
                    "Review discount terms on latest quotation",
                    "Discuss expected decision timeline with primary contact"
                ],
                "suggested_next_actions": [
                    {
                        "title": "Schedule technical review meeting",
                        "action_type": "meeting",
                        "priority": "high"
                    }
                ],
                "suggested_followup_message": "Hi, following up on our recent commercial discussion to confirm next steps."
            }

        # Fallback generic structured dict matching schema properties
        props = schema_dict.get("properties", {})
        result = {}
        for key in props:
            if props[key].get("type") == "array":
                result[key] = ["Mock item 1"]
            elif props[key].get("type") == "integer":
                result[key] = 0
            else:
                result[key] = f"Mock {key} value"
        return result
