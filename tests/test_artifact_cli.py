from pathlib import Path

from english_to_gherkin import artifact_cli
from english_to_gherkin.artifacts import FileBundle
from english_to_gherkin.errors import ProviderError


def arguments(feature: Path, root: Path) -> list[str]:
    return [
        "--feature-file",
        str(feature),
        "--artifact-type",
        "unit-tests",
        "--stack",
        "python-pytest",
        "--repo-root",
        str(root),
    ]


def test_one_candidate_and_no_reviewer_succeeds(tmp_path, monkeypatch):
    feature = tmp_path / "feature.feature"
    feature.write_text(
        "Feature: Example\n  Scenario: Works\n    Given input\n    When processed\n    Then output\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("CANDIDATE_MODEL_1", "openai:model")
    monkeypatch.setenv("CANDIDATE_MODEL_2", "")
    monkeypatch.setenv("CANDIDATE_MODEL_3", "")
    monkeypatch.setenv("REVIEWER_MODEL_SPEC", "")
    monkeypatch.setattr(artifact_cli, "settings_from_model_spec", lambda spec: object())
    monkeypatch.setattr(artifact_cli, "create_provider", lambda settings: object())
    monkeypatch.setattr(
        artifact_cli,
        "generate_bundle",
        lambda *args: FileBundle({"tests/test_generated.py": "def test_ok():\n    assert True\n"}),
    )

    assert artifact_cli.main(arguments(feature, tmp_path)) == 0
    assert (tmp_path / "tests/test_generated.py").exists()


def test_failed_optional_reviewer_uses_candidate(tmp_path, monkeypatch):
    feature = tmp_path / "feature.feature"
    feature.write_text(
        "Feature: Example\n  Scenario: Works\n    Given input\n    When processed\n    Then output\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("CANDIDATE_MODEL_1", "openai:candidate")
    monkeypatch.setenv("CANDIDATE_MODEL_2", "")
    monkeypatch.setenv("CANDIDATE_MODEL_3", "")
    monkeypatch.setenv("REVIEWER_MODEL_SPEC", "openai:reviewer")
    monkeypatch.setattr(artifact_cli, "settings_from_model_spec", lambda spec: spec)
    monkeypatch.setattr(artifact_cli, "create_provider", lambda settings: settings)

    def generate(provider, *args):
        if provider == "openai:reviewer":
            raise ProviderError("reviewer unavailable")
        return FileBundle({"tests/test_generated.py": "def test_ok():\n    assert True\n"})

    monkeypatch.setattr(artifact_cli, "generate_bundle", generate)

    assert artifact_cli.main(arguments(feature, tmp_path)) == 0
    assert (tmp_path / "tests/test_generated.py").exists()
