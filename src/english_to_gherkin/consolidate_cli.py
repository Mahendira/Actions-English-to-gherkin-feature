from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .cli import safe_name
from .config import Settings
from .consolidate import consolidate_feature
from .errors import GeneratorError
from .providers import create_provider


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description="Consolidate candidate Gherkin features")
    result.add_argument("--requirement-name", required=True, type=safe_name)
    result.add_argument("--requirement-file", required=True, type=Path)
    result.add_argument("--candidate-file", required=True, action="append", type=Path)
    result.add_argument("--output-dir", type=Path, default=Path("features"))
    result.add_argument("--output-file", required=True)
    result.add_argument("--overwrite", action="store_true")
    result.add_argument("--max-attempts", type=int, default=3)
    return result


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        if args.max_attempts < 1 or args.max_attempts > 5:
            raise GeneratorError("--max-attempts must be between 1 and 5")

        requirement = args.requirement_file.read_text(encoding="utf-8")
        if not requirement.strip():
            raise GeneratorError("Requirement text cannot be empty")

        candidates = {
            path.name: path.read_text(encoding="utf-8") for path in args.candidate_file
        }
        if len(candidates) != len(args.candidate_file):
            raise GeneratorError("Candidate filenames must be unique")

        filename = safe_name(args.output_file) + ".feature"
        destination = (args.output_dir / filename).resolve()
        if destination.exists() and not args.overwrite:
            raise GeneratorError(f"Output already exists: {destination}. Use --overwrite to replace it")

        feature = consolidate_feature(
            create_provider(Settings.from_env()),
            args.requirement_name,
            requirement,
            candidates,
            args.max_attempts,
        )
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(feature, encoding="utf-8")
        print(destination)
        return 0
    except (GeneratorError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
