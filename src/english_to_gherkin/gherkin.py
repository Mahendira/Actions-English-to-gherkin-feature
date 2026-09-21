from __future__ import annotations

import re

from .errors import ValidationError

FENCE_RE = re.compile(r"^\s*```(?:gherkin|feature)?\s*|\s*```\s*$", re.IGNORECASE)
SCENARIO_RE = re.compile(r"^\s*(Scenario|Scenario Outline):\s*\S+", re.IGNORECASE)
STEP_RE = re.compile(r"^\s*(Given|When|Then|And|But)\s+\S+", re.IGNORECASE)


def clean_generated_text(text: str) -> str:
    cleaned = FENCE_RE.sub("", text.strip()).strip()
    feature_index = next(
        (index for index, line in enumerate(cleaned.splitlines()) if line.strip().lower().startswith("feature:")),
        None,
    )
    if feature_index is not None:
        cleaned = "\n".join(cleaned.splitlines()[feature_index:])
    return cleaned.rstrip() + "\n"


def validate_gherkin(text: str) -> None:
    lines = [line for line in text.splitlines() if line.strip() and not line.lstrip().startswith("#")]
    feature_lines = [line for line in lines if line.strip().lower().startswith("feature:")]
    if len(feature_lines) != 1 or not feature_lines[0].split(":", 1)[1].strip():
        raise ValidationError("Output must contain exactly one non-empty Feature declaration")

    scenario_starts = [index for index, line in enumerate(lines) if SCENARIO_RE.match(line)]
    if not scenario_starts:
        raise ValidationError("Output must contain at least one Scenario or Scenario Outline")

    scenario_starts.append(len(lines))
    for position in range(len(scenario_starts) - 1):
        block = lines[scenario_starts[position] : scenario_starts[position + 1]]
        keywords = [STEP_RE.match(line).group(1).lower() for line in block if STEP_RE.match(line)]
        for required in ("given", "when", "then"):
            if required not in keywords:
                title = block[0].strip()
                raise ValidationError(f"{title} is missing a {required.title()} step")
