import pytest

from english_to_gherkin.errors import ConfigurationError
from english_to_gherkin.model_config import settings_from_model_spec


def test_parses_openrouter_model_with_colon_suffix(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "secret")

    settings = settings_from_model_spec("openrouter:qwen/example:free", 20)

    assert settings.provider == "openai_compatible"
    assert settings.model == "qwen/example:free"
    assert settings.timeout_seconds == 20


def test_rejects_unknown_provider():
    with pytest.raises(ConfigurationError, match="Unsupported provider"):
        settings_from_model_spec("unknown:model", 20)


def test_reports_provider_specific_missing_secret(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    with pytest.raises(ConfigurationError, match="GEMINI_API_KEY"):
        settings_from_model_spec("gemini:example", 20)
