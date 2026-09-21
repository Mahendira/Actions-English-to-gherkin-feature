from __future__ import annotations

import requests

from ..config import Settings
from ..errors import ProviderError
from .base import LlmProvider


class GeminiProvider(LlmProvider):
    def __init__(self, settings: Settings):
        self.settings = settings

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        url = f"{self.settings.api_url}/models/{self.settings.model}:generateContent"
        try:
            response = requests.post(
                url,
                params={"key": self.settings.api_key},
                headers={"Content-Type": "application/json"},
                json={
                    "systemInstruction": {"parts": [{"text": system_prompt}]},
                    "contents": [{"role": "user", "parts": [{"text": user_prompt}]}],
                    "generationConfig": {"temperature": 0.1},
                },
                timeout=self.settings.timeout_seconds,
            )
            response.raise_for_status()
            content = response.json()["candidates"][0]["content"]["parts"][0]["text"]
        except (requests.RequestException, KeyError, IndexError, TypeError, ValueError) as exc:
            raise ProviderError(f"Gemini provider request failed: {exc}") from exc
        if not isinstance(content, str) or not content.strip():
            raise ProviderError("Provider returned empty content")
        return content
