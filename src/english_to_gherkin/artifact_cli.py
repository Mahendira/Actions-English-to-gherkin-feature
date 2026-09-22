from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from .artifacts import (
    ARTIFACT_TYPES,
    STACKS,
    generate_bundle,
    generation_prompt,
    repository_context,
    review_prompt,
    write_bundle,
)
from .errors import GeneratorError
from .model_config import settings_from_model_spec
from .providers import create_provider


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description="Generate a reviewed project artifact")
    result.add_argument("--feature-file", required=True, type=Path)
    result.add_argument("--artifact-type", required=True, choices=ARTIFACT_TYPES)
    result.add_argument("--stack", required=True, choices=STACKS)
    result.add_argument("--repo-root", type=Path, default=Path.cwd())
    result.add_argument("--feedback-file", type=Path)
    result.add_argument("--max-attempts", type=int, default=3)
    return result


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        if args.max_attempts < 1 or args.max_attempts > 5:
            raise GeneratorError("--max-attempts must be between 1 and 5")
        feature = args.feature_file.read_text(encoding="utf-8")
        if not feature.strip():
            raise GeneratorError("Feature file cannot be empty")
        feedback = args.feedback_file.read_text(encoding="utf-8") if args.feedback_file else None
        context = repository_context(args.repo_root)

        candidate_specs = [
            os.getenv("CANDIDATE_MODEL_1", "openai:gpt-4o-mini"),
            os.getenv("CANDIDATE_MODEL_2", "gemini:gemini-3.5-flash-lite"),
            os.getenv("CANDIDATE_MODEL_3", "openrouter:openrouter/free"),
        ]
        system, user = generation_prompt(
            feature, args.artifact_type, args.stack, context, feedback
        )
        candidates = {}
        for index, spec in enumerate(candidate_specs, start=1):
            name = f"candidate-{index}-{spec}"
            try:
                provider = create_provider(settings_from_model_spec(spec))
                candidates[name] = generate_bundle(provider, system, user, args.max_attempts)
            except GeneratorError as exc:
                print(f"WARNING: Skipping {name} candidate: {exc}", file=sys.stderr)
        if len(candidates) < 2:
            raise GeneratorError(
                f"At least two candidate providers must succeed; received {len(candidates)}"
            )

        reviewer_spec = os.getenv("REVIEWER_MODEL_SPEC", "openai:gpt-4o-mini")
        reviewer = create_provider(settings_from_model_spec(reviewer_spec))
        review_system, review_user = review_prompt(
            feature, args.artifact_type, args.stack, candidates, context
        )
        final_bundle = generate_bundle(reviewer, review_system, review_user, args.max_attempts)
        for path in write_bundle(args.repo_root, final_bundle):
            print(path)
        return 0
    except (GeneratorError, OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
