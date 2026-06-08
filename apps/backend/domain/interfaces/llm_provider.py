"""
DeepFeed AI - LLM Provider Interface
Provider abstraction layer as required by TDS §14.3.
All LLM interactions go through this interface — never directly.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class LLMResponse:
    content: str
    model: str
    tokens_used: int
    provider: str


class LLMProvider(ABC):
    """Abstract LLM provider. Concrete implementations for OpenAI, Anthropic, Gemini."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        ...

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 1000,
        temperature: float = 0.3,
    ) -> LLMResponse:
        """Generate a completion from the LLM."""
        ...
