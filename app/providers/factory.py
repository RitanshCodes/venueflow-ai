from __future__ import annotations

from app.core.config import get_settings
from app.providers.base import LLMProvider
from app.providers.mock import MockLLMProvider


def build_provider() -> LLMProvider:
    settings = get_settings()

    if settings.model_provider == "openai":
        from app.providers.openai_provider import OpenAIProvider

        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required when MODEL_PROVIDER=openai")
        return OpenAIProvider(
            api_key=settings.openai_api_key,
            model=settings.openai_model,
        )

    return MockLLMProvider()
