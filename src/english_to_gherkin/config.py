from __future__ import annotations

import os
from dataclasses import dataclass

from .errors import ConfigurationError


@dataclass(frozen=True)
class Settings:
    provider: str
    api_url: str
    api_key: str
    model: str
    timeout_seconds: int = 60

    @classmethod
    def from_env(cls) -> Settings:
        provider = os.getenv("LLM_PROVIDER", "openai_compatible").strip().lower()
        default_urls = {
            "openai_compatible": "https://api.openai.com/v1/chat/completions",
            "gemini": "https://generativelanguage.googleapis.com/v1beta",
        }
        api_url = os.getenv("LLM_API_URL", default_urls.get(provider, "")).strip()
        api_key = os.getenv("LLM_API_KEY", "").strip()
        model = os.getenv("LLM_MODEL", "").strip()

        missing = [
            name
            for name, value in (("LLM_API_URL", api_url), ("LLM_API_KEY", api_key), ("LLM_MODEL", model))
            if not value
        ]
        if missing:
            raise ConfigurationError(f"Missing required environment variable(s): {', '.join(missing)}")

        try:
            timeout = int(os.getenv("LLM_TIMEOUT_SECONDS", "60"))
        except ValueError as exc:
            raise ConfigurationError("LLM_TIMEOUT_SECONDS must be an integer") from exc
        if timeout <= 0:
            raise ConfigurationError("LLM_TIMEOUT_SECONDS must be greater than zero")

        return cls(provider, api_url.rstrip("/"), api_key, model, timeout)
