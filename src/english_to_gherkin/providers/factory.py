from __future__ import annotations

from ..config import Settings
from ..errors import ConfigurationError
from .base import LlmProvider
from .gemini import GeminiProvider
from .openai_compatible import OpenAiCompatibleProvider


def create_provider(settings: Settings) -> LlmProvider:
    providers = {
        "openai_compatible": OpenAiCompatibleProvider,
        "gemini": GeminiProvider,
    }
    provider_class = providers.get(settings.provider)
    if provider_class is None:
        supported = ", ".join(sorted(providers))
        raise ConfigurationError(f"Unsupported LLM_PROVIDER '{settings.provider}'. Use: {supported}")
    return provider_class(settings)
