from __future__ import annotations

import argparse
import sys

from .errors import GeneratorError
from .model_config import settings_from_model_spec
from .providers import create_provider


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description="Verify that an LLM model can answer a request")
    result.add_argument("--model", required=True, help="provider:model")
    result.add_argument("--timeout-seconds", type=int, default=20)
    return result


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        provider = create_provider(settings_from_model_spec(args.model, args.timeout_seconds))
        # A readiness probe must be quick. Normal generation retains the configured retries.
        if hasattr(provider, "MAX_ATTEMPTS"):
            provider.MAX_ATTEMPTS = 1
        provider.generate(
            "You are a readiness probe. Return exactly READY.",
            "Return READY now.",
        )
        print(f"READY: {args.model}")
        return 0
    except (GeneratorError, ValueError) as exc:
        print(f"UNAVAILABLE: {args.model}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
