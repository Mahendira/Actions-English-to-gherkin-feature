from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from .config import Settings
from .errors import GeneratorError
from .generator import generate_feature
from .providers import create_provider


def safe_name(value: str) -> str:
    stem = Path(value).stem
    normalized = re.sub(r"[^A-Za-z0-9_-]+", "_", stem).strip("_")
    if not normalized:
        raise argparse.ArgumentTypeError("requirement name must contain letters or numbers")
    return normalized


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description="Convert an English requirement into Gherkin")
    result.add_argument("--requirement-name", required=True, type=safe_name)
    source = result.add_mutually_exclusive_group(required=True)
    source.add_argument("--requirement-text", help="Requirement supplied directly")
    source.add_argument("--requirement-file", type=Path, help="UTF-8 text requirement file")
    result.add_argument("--output-dir", type=Path, default=Path("features"))
    result.add_argument("--output-file", help="Optional output filename; defaults to <name>.feature")
    result.add_argument("--overwrite", action="store_true", help="Replace an existing feature file")
    return result


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        requirement = (
            args.requirement_text
            if args.requirement_text is not None
            else args.requirement_file.read_text(encoding="utf-8")
        )
        if not requirement.strip():
            raise GeneratorError("Requirement text cannot be empty")

        filename = safe_name(args.output_file or args.requirement_name) + ".feature"
        destination = (args.output_dir / filename).resolve()
        if destination.exists() and not args.overwrite:
            raise GeneratorError(f"Output already exists: {destination}. Use --overwrite to replace it")

        settings = Settings.from_env()
        feature = generate_feature(create_provider(settings), args.requirement_name, requirement)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(feature, encoding="utf-8")
        print(destination)
        return 0
    except (GeneratorError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
