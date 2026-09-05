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
        """Calls Gemini API to generate text output."""
        if not self.api_key:
            raise DealFlowException(
                message="Gemini API Key is not configured on the server.",
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE
            )

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
        async with httpx.AsyncClient(timeout=timeout) as client:
            try:
                response = await client.post(url, json=payload)
                if response.status_code != 200:
                    logger.error(f"Gemini API returned HTTP {response.status_code}: {response.text}")
                    raise DealFlowException(
                        message=f"AI Provider service error (HTTP {response.status_code}).",
                        status_code=status.HTTP_503_SERVICE_UNAVAILABLE
                    )

                data = response.json()
                try:
                    candidates = data.get("candidates", [])
                    if not candidates:
                        raise DealFlowException(
                            message="AI Provider returned empty candidate output.",
                            status_code=status.HTTP_502_BAD_GATEWAY
                        )
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if not parts:
                        raise DealFlowException(
                            message="AI Provider returned malformed content structure.",
                            status_code=status.HTTP_502_BAD_GATEWAY
                        )
                    return parts[0].get("text", "")
                except (KeyError, IndexError, TypeError) as exc:
                    logger.error(f"Failed to parse Gemini response payload: {exc}")
                    raise DealFlowException(
                        message="AI Provider response parsing failed.",
                        status_code=status.HTTP_502_BAD_GATEWAY
                    )

            except (httpx.TimeoutException, httpx.RequestError) as exc:
                logger.error(f"Gemini API communication failed: {exc}")
                raise DealFlowException(
                    message="AI Provider is temporarily unreachable or timed out.",
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE
                )

    async def generate_structured(
        self,
        system_instruction: str,
        user_prompt: str,
        schema_dict: Dict[str, Any],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        """Calls Gemini API instructing JSON response format and parses output."""
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

        try:
            return json.loads(cleaned_text)
        except json.JSONDecodeError as exc:
            logger.error(f"Failed to parse JSON from AI response: {exc}. Raw text: {cleaned_text}")
            raise DealFlowException(
                message="AI Provider generated malformed structured output.",
                status_code=status.HTTP_502_BAD_GATEWAY
            )
