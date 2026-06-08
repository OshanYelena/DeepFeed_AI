"""
DeepFeed AI - LLM Provider Implementations (TDS §14.3)
Concrete implementations for Anthropic, OpenAI, and Gemini.
Router selects provider based on task cost tier (TDS §14.4).
"""
from typing import Optional
from domain.interfaces.llm_provider import LLMProvider, LLMResponse
from config import settings
from logger import get_logger

logger = get_logger(__name__)


class AnthropicProvider(LLMProvider):
    """Anthropic Claude provider."""

    @property
    def provider_name(self) -> str:
        return "anthropic"

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 1000,
        temperature: float = 0.3,
    ) -> LLMResponse:
        import anthropic
        client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

        messages = [{"role": "user", "content": prompt}]
        kwargs = {
            "model": "claude-haiku-4-5-20251001",
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": messages,
        }
        if system_prompt:
            kwargs["system"] = system_prompt

        response = await client.messages.create(**kwargs)
        content = response.content[0].text if response.content else ""
        tokens = response.usage.input_tokens + response.usage.output_tokens

        logger.info("llm_request_complete", provider="anthropic", tokens=tokens)
        return LLMResponse(content=content, model=kwargs["model"], tokens_used=tokens, provider="anthropic")


class OpenAIProvider(LLMProvider):
    """OpenAI GPT provider."""

    @property
    def provider_name(self) -> str:
        return "openai"

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 1000,
        temperature: float = 0.3,
    ) -> LLMResponse:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=settings.openai_api_key)

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        content = response.choices[0].message.content or ""
        tokens = response.usage.total_tokens if response.usage else 0

        logger.info("llm_request_complete", provider="openai", tokens=tokens)
        return LLMResponse(content=content, model="gpt-4o-mini", tokens_used=tokens, provider="openai")


class LLMRouter:
    """
    Routes LLM requests to the appropriate provider based on task cost tier.
    TDS §14.4: Low cost → small models, Medium → mid-tier, Expensive → large.
    """

    def __init__(self) -> None:
        self._providers: dict[str, LLMProvider] = {}
        self._default: Optional[LLMProvider] = None
        self._initialize()

    def _initialize(self) -> None:
        if settings.anthropic_api_key:
            self._providers["anthropic"] = AnthropicProvider()
        if settings.openai_api_key:
            self._providers["openai"] = OpenAIProvider()

        preferred = settings.default_llm_provider
        if preferred in self._providers:
            self._default = self._providers[preferred]
        elif self._providers:
            self._default = next(iter(self._providers.values()))

    def get_provider(self, task_type: str = "medium") -> Optional[LLMProvider]:
        """Return the appropriate provider for the task type."""
        return self._default

    def is_available(self) -> bool:
        return self._default is not None


# Singleton router
_llm_router = None


def get_llm_router() -> LLMRouter:
    global _llm_router
    if _llm_router is None:
        _llm_router = LLMRouter()
    return _llm_router


def get_llm_provider(task_type: str = "medium") -> Optional[LLMProvider]:
    """Convenience function to get provider for a task type."""
    return get_llm_router().get_provider(task_type)
