from __future__ import annotations

import os

from .config import Settings
from .errors import ConfigurationError

PROVIDERS = {
    "openai": ("OPENAI", "openai_compatible", "https://api.openai.com/v1/chat/completions"),
    "gemini": ("GEMINI", "gemini", "https://generativelanguage.googleapis.com/v1beta"),
    "openrouter": (
        "OPENROUTER",
        "openai_compatible",
        "https://openrouter.ai/api/v1/chat/completions",
    ),
}


def settings_from_model_spec(spec: str, timeout_seconds: int | None = None) -> Settings:
    provider_name, separator, model = spec.strip().partition(":")
    provider_name = provider_name.lower()
    model = model.strip()
    if not separator or not model:
        raise ConfigurationError(
            f"Invalid model selection '{spec}'. Expected provider:model, for example "
            "openai:gpt-4o-mini"
        )
    if provider_name not in PROVIDERS:
        supported = ", ".join(sorted(PROVIDERS))
        raise ConfigurationError(f"Unsupported provider '{provider_name}'. Use one of: {supported}")

    prefix, provider_type, default_url = PROVIDERS[provider_name]
    api_key = os.getenv(f"{prefix}_API_KEY", "").strip()
    api_url = os.getenv(f"{prefix}_API_URL", default_url).strip().rstrip("/")
    if not api_key:
        raise ConfigurationError(f"Missing required secret: {prefix}_API_KEY")

    if timeout_seconds is None:
        try:
            timeout_seconds = int(os.getenv("LLM_TIMEOUT_SECONDS", "60"))
        except ValueError as exc:
            raise ConfigurationError("LLM_TIMEOUT_SECONDS must be an integer") from exc
    if timeout_seconds <= 0:
        raise ConfigurationError("LLM timeout must be greater than zero")

    return Settings(provider_type, api_url, api_key, model, timeout_seconds)
