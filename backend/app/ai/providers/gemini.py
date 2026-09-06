import json
import logging
from typing import Dict, Any, Optional
import httpx
from fastapi import status

from app.ai.base import AbstractAIProvider
from app.core.config import settings
from app.core.exceptions import DealFlowException

logger = logging.getLogger("dealflow360.ai.gemini")


class GeminiAIProvider(AbstractAIProvider):
    """Google Gemini REST API v1beta Provider implementation."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model = model or settings.GEMINI_MODEL
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"

    async def generate_content(
        self,
        system_instruction: str,
        user_prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> str:
        """Calls Gemini API to generate text output with fallback to MockAIProvider."""
        if not self.api_key or self.api_key.startswith("your_"):
            from app.ai.providers.mock import MockAIProvider
            return await MockAIProvider().generate_content(system_instruction, user_prompt, temperature, max_tokens)

        url = f"{self.base_url}/models/{self.model}:generateContent?key={self.api_key}"
        payload = {
            "system_instruction": {
                "parts": [{"text": system_instruction}]
            },
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": user_prompt}]
                }
            ],
            "generationConfig": {
                "temperature": temperature if temperature is not None else settings.AI_TEMPERATURE,
                "maxOutputTokens": max_tokens if max_tokens is not None else settings.AI_MAX_OUTPUT_TOKENS,
            }
        }

        timeout = httpx.Timeout(settings.AI_TIMEOUT_SECONDS)
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(url, json=payload)
                if response.status_code != 200:
                    logger.warning(f"Gemini API returned HTTP {response.status_code}. Falling back to MockAIProvider.")
                    from app.ai.providers.mock import MockAIProvider
                    return await MockAIProvider().generate_content(system_instruction, user_prompt, temperature, max_tokens)

                data = response.json()
                candidates = data.get("candidates", [])
                if candidates and "content" in candidates[0]:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if parts:
                        return parts[0].get("text", "")
        except Exception as exc:
            logger.warning(f"Gemini API call failed: {exc}. Falling back to MockAIProvider.")

        from app.ai.providers.mock import MockAIProvider
        return await MockAIProvider().generate_content(system_instruction, user_prompt, temperature, max_tokens)

    async def generate_structured(
        self,
        system_instruction: str,
        user_prompt: str,
        schema_dict: Dict[str, Any],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        """Calls Gemini API instructing JSON response format with fallback to MockAIProvider."""
        try:
            json_instruction = (
                f"{system_instruction}\n\n"
                "CRITICAL FORMAT REQUIREMENT: Respond ONLY with a valid JSON object matching this schema:\n"
                f"{json.dumps(schema_dict, indent=2)}\n"
                "Do NOT include markdown formatting like ```json or trailing text."
            )

            raw_text = await self.generate_content(json_instruction, user_prompt, temperature, max_tokens)
            cleaned_text = raw_text.strip()
            if cleaned_text.startswith("```json"):
                cleaned_text = cleaned_text.replace("```json", "", 1)
            if cleaned_text.startswith("```"):
                cleaned_text = cleaned_text.replace("```", "", 1)
            if cleaned_text.endswith("```"):
                cleaned_text = cleaned_text[:-3].strip()

            return json.loads(cleaned_text)
        except Exception as exc:
            logger.warning(f"Gemini structured generation failed: {exc}. Falling back to MockAIProvider.")
            from app.ai.providers.mock import MockAIProvider
            return await MockAIProvider().generate_structured(system_instruction, user_prompt, schema_dict, temperature, max_tokens)
