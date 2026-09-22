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
from .config import Settings
from .errors import GeneratorError
from .providers import create_provider


def _settings(prefix: str, provider: str, default_url: str, default_model: str = "") -> Settings:
    key = os.getenv(f"{prefix}_API_KEY", "").strip()
    model = os.getenv(f"{prefix}_MODEL", default_model).strip()
    url = os.getenv(f"{prefix}_API_URL", default_url).strip()
    missing = [name for name, value in ((f"{prefix}_API_KEY", key), (f"{prefix}_MODEL", model)) if not value]
    if missing:
        raise GeneratorError(f"Missing required environment variable(s): {', '.join(missing)}")
    return Settings(provider, url.rstrip("/"), key, model, int(os.getenv("LLM_TIMEOUT_SECONDS", "120")))


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

        providers = {
            "openai": create_provider(
                _settings("OPENAI", "openai_compatible", "https://api.openai.com/v1/chat/completions")
            ),
            "gemini": create_provider(
                _settings("GEMINI", "gemini", "https://generativelanguage.googleapis.com/v1beta")
            ),
            "openrouter": create_provider(
                _settings(
                    "OPENROUTER",
                    "openai_compatible",
                    "https://openrouter.ai/api/v1/chat/completions",
                )
            ),
        }
        system, user = generation_prompt(
            feature, args.artifact_type, args.stack, context, feedback
        )
        candidates = {
            name: generate_bundle(provider, system, user, args.max_attempts)
            for name, provider in providers.items()
        }

        reviewer = create_provider(
            _settings(
                "REVIEWER",
                "openai_compatible",
                "https://openrouter.ai/api/v1/chat/completions",
                "qwen/qwen3.8-27b:free",
            )
        )
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
