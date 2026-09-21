from __future__ import annotations

from collections.abc import Mapping

from .errors import ValidationError
from .gherkin import clean_generated_text, validate_gherkin
from .providers.base import LlmProvider

REVIEW_SYSTEM_PROMPT = """You are an independent senior BDD reviewer.
Consolidate multiple candidate Gherkin features into one authoritative feature.

Rules:
- Treat the original requirement as the only source of truth.
- Preserve every explicit functional, security, error-handling, performance,
  metadata, pagination, logging, and audit requirement that is testable.
- Resolve candidate contradictions by following the original requirement.
- Remove duplicate scenarios and combine overlapping coverage.
- Do not invent endpoints, fields, status codes, limits, or business behavior.
- Every Scenario and Scenario Outline must contain Given, When, and Then steps.
- Make steps observable and implementation-independent.
- Use tags such as @performance or @audit when they improve test organization.
- Return only valid Gherkin, without Markdown fences or commentary.
"""


def review_prompt(
    requirement_name: str,
    requirement_text: str,
    candidates: Mapping[str, str],
    validation_feedback: str | None = None,
) -> str:
    candidate_text = "\n\n".join(
        f"--- Candidate: {name} ---\n{content.strip()}" for name, content in candidates.items()
    )
    feedback = ""
    if validation_feedback:
        feedback = (
            "\n\nThe previous consolidation was rejected by the Gherkin validator:\n"
            f"{validation_feedback}\nRegenerate the complete corrected feature."
        )
    return f"""Feature name: {requirement_name}

--- Authoritative original requirement ---
{requirement_text.strip()}

--- Candidate features to review ---
{candidate_text}

Produce one comprehensive, non-duplicative Gherkin feature that is fully
traceable to the authoritative requirement.{feedback}"""


def consolidate_feature(
    provider: LlmProvider,
    requirement_name: str,
    requirement_text: str,
    candidates: Mapping[str, str],
    max_attempts: int = 3,
) -> str:
    if not candidates:
        raise ValidationError("At least one candidate feature is required")
    for content in candidates.values():
        validate_gherkin(content)

    feedback: str | None = None
    for attempt in range(1, max_attempts + 1):
        raw = provider.generate(
            REVIEW_SYSTEM_PROMPT,
            review_prompt(requirement_name, requirement_text, candidates, feedback),
        )
        feature = clean_generated_text(raw)
        try:
            validate_gherkin(feature)
            return feature
        except ValidationError as exc:
            feedback = f"Attempt {attempt}: {exc}"

    raise ValidationError(
        f"Reviewer did not produce valid Gherkin after {max_attempts} attempts: {feedback}"
    )
