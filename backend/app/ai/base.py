from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class AbstractAIProvider(ABC):
    """Abstract interface defining contract for AI intelligence providers."""

    @abstractmethod
    async def generate_content(
        self,
        system_instruction: str,
        user_prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> str:
        """Generates raw text response from provider model."""
        pass

    @abstractmethod
    async def generate_structured(
        self,
        system_instruction: str,
        user_prompt: str,
        schema_dict: Dict[str, Any],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        """Generates validated JSON structured output matching specified JSON schema."""
        pass
