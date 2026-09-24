from __future__ import annotations

import json
import re
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from .errors import GeneratorError, ValidationError
from .providers.base import LlmProvider

STACKS = ("java-maven", "java-gradle", "python-pytest")
ARTIFACT_TYPES = ("step-definitions", "unit-tests", "application-code")
MAX_FILES = 40
MAX_FILE_BYTES = 200_000


@dataclass(frozen=True)
class FileBundle:
    files: dict[str, str]


PRODUCTION_SOURCE_SUFFIXES = {
    ".c",
    ".cc",
    ".cpp",
    ".cs",
    ".go",
    ".h",
    ".hpp",
    ".java",
    ".js",
    ".jsx",
    ".kt",
    ".kts",
    ".py",
    ".rs",
    ".ts",
    ".tsx",
}


def validate_application_layout(bundle: FileBundle, source_directory: str) -> None:
    source = PurePosixPath(source_directory)
    for raw_path in bundle.files:
        path = PurePosixPath(raw_path)
        if path.parts and path.parts[0] == "app":
            raise ValidationError(
                f"Production application files must use {source_directory}/, not app/: {raw_path}"
            )
        if path.suffix.lower() not in PRODUCTION_SOURCE_SUFFIXES:
            continue
        under_source = path.parts[: len(source.parts)] == source.parts
        test_source = path.parts and path.parts[0] in {"test", "tests"}
        if not under_source and not test_source:
            raise ValidationError(
                f"Source file must be under {source_directory}/ or tests/: {raw_path}"
            )


def _extract_json(text: str) -> dict:
    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start < 0 or end < start:
        raise ValidationError("Model output does not contain a JSON object")
    try:
        value = json.loads(cleaned[start : end + 1])
    except json.JSONDecodeError as exc:
        raise ValidationError(f"Model output is not valid JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise ValidationError("Model output must be a JSON object")
    return value


def parse_bundle(text: str) -> FileBundle:
    value = _extract_json(text)
    raw_files = value.get("files")
    if not isinstance(raw_files, list) or not raw_files:
        raise ValidationError("JSON must contain a non-empty files array")
    if len(raw_files) > MAX_FILES:
        raise ValidationError(f"Bundle exceeds the {MAX_FILES}-file limit")

    files: dict[str, str] = {}
    for item in raw_files:
        if not isinstance(item, dict):
            raise ValidationError("Each files entry must be an object")
        path = item.get("path")
        content = item.get("content")
        if not isinstance(path, str) or not isinstance(content, str):
            raise ValidationError("Each file requires string path and content fields")
        normalized = PurePosixPath(path)
        if (
            normalized.is_absolute()
            or ".." in normalized.parts
            or path.startswith("~")
            or "\\" in path
        ):
            raise ValidationError(f"Unsafe generated path: {path}")
        if not normalized.parts or any(part.startswith(".") for part in normalized.parts):
            raise ValidationError(f"Generated path is not allowed: {path}")
        normalized_path = normalized.as_posix()
        if normalized_path in files:
            raise ValidationError(f"Duplicate generated path: {normalized_path}")
        if len(content.encode("utf-8")) > MAX_FILE_BYTES:
            raise ValidationError(f"Generated file is too large: {normalized_path}")
        files[normalized_path] = content.rstrip() + "\n"
    return FileBundle(files)


def artifact_instructions(artifact_type: str, stack: str) -> str:
    stack_rules = {
        "java-maven": "Use Java 21, Spring Boot, Maven, JUnit 5, Mockito, Cucumber Java, and JaCoCo.",
        "java-gradle": "Use Java 21, Spring Boot, Gradle, JUnit 5, Mockito, Cucumber Java, and JaCoCo.",
        "python-pytest": "Use Python 3.11+, pytest, pytest-bdd, and pytest-cov.",
    }
    artifact_rules = {
        "step-definitions": (
            "Generate executable BDD step definitions and only the minimal test configuration/support "
            "needed to discover them. Do not generate application implementation."
        ),
        "unit-tests": (
            "Generate isolated unit tests derived from the feature's behavior, including boundary and "
            "error cases. Add only minimal test dependencies/configuration when absent. Do not generate "
            "application implementation."
        ),
        "application-code": (
            "Generate or repair production application code implementing the feature. Preserve existing "
            "tests and public behavior. Add minimal build configuration only when required."
        ),
    }
    return f"{stack_rules[stack]}\n{artifact_rules[artifact_type]}"


def generation_prompt(
    feature_text: str,
    artifact_type: str,
    stack: str,
    repository_context: str,
    feedback: str | None = None,
    source_directory: str = "src",
) -> tuple[str, str]:
    system = """You are a senior software engineer working in a pull-request-only automation.
Return only JSON in this exact shape:
{"files":[{"path":"repository/relative/path","content":"complete file content"}]}
Do not use Markdown fences. Use safe repository-relative paths. Return complete files, not patches.
Do not modify CI workflows, secrets, generated coverage output, or the authoritative feature file.
Do not add behavior that is unsupported by the feature.
"""
    repair = f"\n\nBuild/test feedback to address:\n{feedback[-12000:]}" if feedback else ""
    layout = ""
    if artifact_type == "application-code":
        layout = f"""

Application repository layout:
- Put all production source code and runtime assets under `{source_directory}/`.
- Do not create an `app/` directory or place production source at the repository root.
- Preserve the requirement text, authoritative feature files, and existing tests.
- Keep build, dependency, container, and infrastructure-as-code files at the repository root
  when they are needed to build or deploy the application.
- When the feature describes cloud infrastructure, include the minimal deployable infrastructure
  configuration required by the selected stack.
"""
    user = f"""Artifact: {artifact_type}
Stack: {stack}

Engineering rules:
{artifact_instructions(artifact_type, stack)}
{layout}

Authoritative Gherkin feature:
{feature_text.strip()}

Existing repository context:
{repository_context}
{repair}

Generate the smallest coherent file set required for this artifact."""
    return system, user


def review_prompt(
    feature_text: str,
    artifact_type: str,
    stack: str,
    candidates: Mapping[str, FileBundle],
    repository_context: str,
    source_directory: str = "src",
) -> tuple[str, str]:
    system = """You are an independent senior code reviewer and consolidator.
Return only JSON in this exact shape:
{"files":[{"path":"repository/relative/path","content":"complete file content"}]}
The Gherkin feature is the only source of truth. Compare all candidates, resolve conflicts,
remove duplication, preserve useful coverage, and produce one coherent implementation.
Never invent behavior. Never output Markdown or patches. Use safe repository-relative paths.
"""
    rendered = []
    for name, bundle in candidates.items():
        rendered.append(
            f"--- {name} ---\n"
            + json.dumps(
                {"files": [{"path": path, "content": content} for path, content in bundle.files.items()]},
                ensure_ascii=False,
            )
        )
    layout = ""
    if artifact_type == "application-code":
        layout = f"""

Application repository layout:
- Put all production source code and runtime assets under `{source_directory}/`.
- Do not create an `app/` directory or place production source at the repository root.
- Preserve requirement text, feature files, tests, and required deployment configuration.
"""
    user = f"""Artifact: {artifact_type}
Stack: {stack}

Engineering rules:
{artifact_instructions(artifact_type, stack)}
{layout}

Authoritative Gherkin feature:
{feature_text.strip()}

Existing repository context:
{repository_context}

Candidate bundles:
{chr(10).join(rendered)}

Return the consolidated file bundle."""
    return system, user


def generate_bundle(
    provider: LlmProvider,
    system_prompt: str,
    user_prompt: str,
    max_attempts: int = 3,
    validator: Callable[[FileBundle], None] | None = None,
) -> FileBundle:
    feedback = ""
    for _ in range(max_attempts):
        raw = provider.generate(system_prompt, user_prompt + feedback)
        try:
            bundle = parse_bundle(raw)
            if validator:
                validator(bundle)
            return bundle
        except ValidationError as exc:
            feedback = f"\n\nPrevious JSON was rejected: {exc}. Return the complete corrected JSON."
    raise ValidationError(f"Model failed to produce a valid file bundle after {max_attempts} attempts")


def repository_context(root: Path, max_chars: int = 40_000) -> str:
    allowed_names = {
        "pom.xml",
        "build.gradle",
        "build.gradle.kts",
        "settings.gradle",
        "settings.gradle.kts",
        "pyproject.toml",
        "requirements.txt",
        "requirements-dev.txt",
    }
    allowed_suffixes = {".java", ".py"}
    ignored_parts = {".git", ".venv", "target", "build", "dist", "htmlcov", "node_modules"}
    sections: list[str] = []
    used = 0
    for path in sorted(root.rglob("*")):
        if not path.is_file() or any(part in ignored_parts for part in path.parts):
            continue
        relative = path.relative_to(root).as_posix()
        if path.name not in allowed_names and path.suffix not in allowed_suffixes:
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        section = f"--- {relative} ---\n{content}\n"
        if used + len(section) > max_chars:
            sections.append("[repository context truncated]")
            break
        sections.append(section)
        used += len(section)
    return "\n".join(sections) or "[no relevant source or build files found]"


def write_bundle(root: Path, bundle: FileBundle) -> list[Path]:
    root = root.resolve()
    written: list[Path] = []
    for relative, content in bundle.files.items():
        destination = (root / relative).resolve()
        if destination != root and root not in destination.parents:
            raise GeneratorError(f"Generated path escapes repository: {relative}")
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(content, encoding="utf-8")
        written.append(destination)
    return written
