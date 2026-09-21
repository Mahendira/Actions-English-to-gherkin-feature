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
        except requests.HTTPError as exc:
            response = exc.response
            try:
                error_data = response.json()
                detail = error_data.get("error", {}).get("message", response.text)
            except (AttributeError, ValueError):
                detail = response.text if response is not None else str(exc)
            status = response.status_code if response is not None else "unknown"
            raise ProviderError(f"Provider returned HTTP {status}: {detail[:1000]}") from exc
        except (requests.RequestException, KeyError, IndexError, TypeError, ValueError) as exc:
            raise ProviderError(f"OpenAI-compatible provider request failed: {exc}") from exc
        if not isinstance(content, str) or not content.strip():
            raise ProviderError("Provider returned empty content")
        return content
