from __future__ import annotations

from abc import ABC, abstractmethod


class LlmProvider(ABC):
    @abstractmethod
    def generate(self, system_prompt: str, user_prompt: str) -> str:
        """Return generated text or raise ProviderError."""
