from __future__ import annotations

import requests

from ..config import Settings
from ..errors import ProviderError
from .base import LlmProvider


class OpenAiCompatibleProvider(LlmProvider):
    """Works with OpenAI, OpenRouter, Groq, and compatible local gateways."""

    def __init__(self, settings: Settings):
        self.settings = settings

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        try:
            response = requests.post(
                self.settings.api_url,
                headers={
                    "Authorization": f"Bearer {self.settings.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.settings.model,
                    "temperature": 0.1,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                },
                timeout=self.settings.timeout_seconds,
            )
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"]
        except (requests.RequestException, KeyError, IndexError, TypeError, ValueError) as exc:
            raise ProviderError(f"OpenAI-compatible provider request failed: {exc}") from exc
        if not isinstance(content, str) or not content.strip():
            raise ProviderError("Provider returned empty content")
        return content
