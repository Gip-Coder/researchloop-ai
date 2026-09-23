"""
Factory for creating LLM providers according to configuration and environment.
"""

from __future__ import annotations

from backend.agent.core.config import get_settings
from backend.agent.models.research import ResearchConfig
from backend.providers.llm.base import LLMProvider
from backend.providers.llm.mock import MockLLMProvider
from backend.providers.llm.openai import OpenAIProvider
from backend.providers.llm.anthropic import AnthropicProvider
from backend.providers.llm.gemini import GeminiProvider


def get_llm_provider(config: ResearchConfig | None = None) -> LLMProvider:
    """Instantiate and return the configured LLM provider."""
    settings = get_settings()

    # Determine provider key
    provider_name = "mock"
    model_override = None
    temperature = 0.2

    if config is not None:
        if config.mock_mode or settings.is_mock_mode:
            provider_name = "mock"
        else:
            provider_name = config.llm_provider or settings.llm_provider
        model_override = config.llm_model
        temperature = config.temperature
    else:
        provider_name = "mock" if settings.is_mock_mode else settings.llm_provider
        model_override = settings.llm_model

    provider_name = provider_name.lower().strip()

    if provider_name == "openai":
        return OpenAIProvider(model=model_override, temperature=temperature)
    elif provider_name == "anthropic":
        return AnthropicProvider(model=model_override, temperature=temperature)
    elif provider_name == "gemini":
        return GeminiProvider(model=model_override, temperature=temperature)
    elif provider_name == "mock":
        return MockLLMProvider(model=model_override or "mock-gpt-4o", temperature=temperature)
    else:
        # Fallback to Mock if unrecognized provider
        return MockLLMProvider(model=model_override or "mock-gpt-4o", temperature=temperature)

