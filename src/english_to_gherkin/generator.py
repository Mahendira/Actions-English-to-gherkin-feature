from __future__ import annotations

from .gherkin import clean_generated_text, validate_gherkin
from .prompts import SYSTEM_PROMPT, user_prompt
from .providers.base import LlmProvider


def generate_feature(provider: LlmProvider, requirement_name: str, requirement_text: str) -> str:
    raw = provider.generate(SYSTEM_PROMPT, user_prompt(requirement_name, requirement_text))
    feature = clean_generated_text(raw)
    validate_gherkin(feature)
    return feature
