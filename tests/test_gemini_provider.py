import requests

from english_to_gherkin.config import Settings
from english_to_gherkin.providers.gemini import GeminiProvider


class FakeResponse:
    def __init__(self, status_code: int, content: str = ""):
        self.status_code = status_code
        self.content = content

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise requests.HTTPError(f"HTTP {self.status_code}")

    def json(self) -> dict:
        return {"candidates": [{"content": {"parts": [{"text": self.content}]}}]}


def provider() -> GeminiProvider:
    return GeminiProvider(Settings("gemini", "https://example.test", "key", "model", 120))


def test_retries_transient_http_status(monkeypatch):
    responses = iter([FakeResponse(503), FakeResponse(200, "generated feature")])
    monkeypatch.setattr(
        "english_to_gherkin.providers.gemini.requests.post",
        lambda *args, **kwargs: next(responses),
    )
    monkeypatch.setattr("english_to_gherkin.providers.gemini.time.sleep", lambda seconds: None)

    assert provider().generate("system", "user") == "generated feature"


def test_retries_read_timeout(monkeypatch):
    results = iter([requests.ReadTimeout("slow"), FakeResponse(200, "generated feature")])

    def post(*args, **kwargs):
        result = next(results)
        if isinstance(result, Exception):
            raise result
        return result

    monkeypatch.setattr("english_to_gherkin.providers.gemini.requests.post", post)
    monkeypatch.setattr("english_to_gherkin.providers.gemini.time.sleep", lambda seconds: None)

    assert provider().generate("system", "user") == "generated feature"
