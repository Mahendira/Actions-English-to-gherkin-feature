from __future__ import annotations

import time
from typing import ClassVar

import requests

from ..config import Settings
from ..errors import ProviderError
from .base import LlmProvider


class GeminiProvider(LlmProvider):
    MAX_RETRIES = 3
    MAX_ATTEMPTS = MAX_RETRIES + 1
    RETRYABLE_STATUS_CODES: ClassVar[frozenset[int]] = frozenset({429, 500, 502, 503, 504})
    RETRY_DELAYS_SECONDS = (5, 15, 30)

    def __init__(self, settings: Settings):
        self.settings = settings

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        url = f"{self.settings.api_url}/models/{self.settings.model}:generateContent"
        for attempt in range(1, self.MAX_ATTEMPTS + 1):
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
                if (
                    response.status_code in self.RETRYABLE_STATUS_CODES
                    and attempt < self.MAX_ATTEMPTS
                ):
                    self._wait_before_retry(attempt, f"HTTP {response.status_code}")
                    continue
                response.raise_for_status()
                content = response.json()["candidates"][0]["content"]["parts"][0]["text"]
                if not isinstance(content, str) or not content.strip():
                    raise ProviderError("Gemini provider returned empty content")
                return content
            except (requests.Timeout, requests.ConnectionError) as exc:
                if attempt < self.MAX_ATTEMPTS:
                    self._wait_before_retry(attempt, type(exc).__name__)
                    continue
                raise ProviderError(
                    f"Gemini provider request failed after {self.MAX_ATTEMPTS} attempts: {exc}"
                ) from exc
            except (requests.RequestException, KeyError, IndexError, TypeError, ValueError) as exc:
                raise ProviderError(f"Gemini provider request failed: {exc}") from exc

        raise ProviderError("Gemini provider request failed after all retry attempts")

    def _wait_before_retry(self, attempt: int, reason: str) -> None:
        delay = self.RETRY_DELAYS_SECONDS[attempt - 1]
        print(
            f"WARNING: Gemini request attempt {attempt} failed ({reason}); "
            f"retrying in {delay} seconds.",
            flush=True,
        )
        time.sleep(delay)
