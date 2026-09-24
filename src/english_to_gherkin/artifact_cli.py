from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path, PurePosixPath

from .artifacts import (
    ARTIFACT_TYPES,
    STACKS,
    generate_bundle,
    generation_prompt,
    repository_context,
    review_prompt,
    validate_application_layout,
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
    result.add_argument("--source-directory", default="src")
    return result


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        if args.max_attempts < 1 or args.max_attempts > 5:
            raise GeneratorError("--max-attempts must be between 1 and 5")
        source_directory = PurePosixPath(args.source_directory)
        if (
            source_directory.is_absolute()
            or ".." in source_directory.parts
            or not source_directory.parts
            or any(part.startswith(".") for part in source_directory.parts)
        ):
            raise GeneratorError("--source-directory must be a safe repository-relative path")
        source_directory_text = source_directory.as_posix()
        feature = args.feature_file.read_text(encoding="utf-8")
        if not feature.strip():
            raise GeneratorError("Feature file cannot be empty")
        feedback = args.feedback_file.read_text(encoding="utf-8") if args.feedback_file else None
        context = repository_context(args.repo_root)

        candidate_specs = [
            os.getenv("CANDIDATE_MODEL_1", "openai:gpt-4o-mini"),
            os.getenv("CANDIDATE_MODEL_2", ""),
            os.getenv("CANDIDATE_MODEL_3", ""),
        ]
        candidate_specs = [spec.strip() for spec in candidate_specs if spec.strip()]
        system, user = generation_prompt(
            feature,
            args.artifact_type,
            args.stack,
            context,
            feedback,
            source_directory_text,
        )
        candidates = {}
        validator = None
        if args.artifact_type == "application-code":
            validator = lambda bundle: validate_application_layout(
                bundle, source_directory_text
            )
        for index, spec in enumerate(candidate_specs, start=1):
            name = f"candidate-{index}-{spec}"
            try:
                provider = create_provider(settings_from_model_spec(spec))
                candidates[name] = generate_bundle(
                    provider, system, user, args.max_attempts, validator
                )
            except GeneratorError as exc:
                print(f"WARNING: Skipping {name} candidate: {exc}", file=sys.stderr)
        if not candidates:
            raise GeneratorError("At least one candidate provider must succeed")

        reviewer_spec = os.getenv("REVIEWER_MODEL_SPEC", "").strip()
        final_bundle = next(iter(candidates.values()))
        if reviewer_spec:
            try:
                reviewer = create_provider(settings_from_model_spec(reviewer_spec))
                review_system, review_user = review_prompt(
                    feature,
                    args.artifact_type,
                    args.stack,
                    candidates,
                    context,
                    source_directory_text,
                )
                final_bundle = generate_bundle(
                    reviewer,
                    review_system,
                    review_user,
                    args.max_attempts,
                    validator,
                )
            except GeneratorError as exc:
                print(
                    f"WARNING: Reviewer {reviewer_spec} failed; using the first successful "
                    f"candidate: {exc}",
                    file=sys.stderr,
                )
        else:
            print(
                "INFO: No reviewer selected; using the first successful candidate.",
                file=sys.stderr,
            )
        for path in write_bundle(args.repo_root, final_bundle):
            print(path)
        return 0
    except (GeneratorError, OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
