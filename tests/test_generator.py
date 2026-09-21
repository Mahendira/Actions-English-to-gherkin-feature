from english_to_gherkin.generator import generate_feature
from english_to_gherkin.providers.base import LlmProvider


class FakeProvider(LlmProvider):
    def generate(self, system_prompt: str, user_prompt: str) -> str:
        assert "implementation-independent" in system_prompt
        assert "Search API" in user_prompt
        return """Feature: Search API
  Scenario: Search succeeds
    Given searchable products exist
    When the user searches for a product
    Then matching products are returned
"""


def test_generator_is_independent_of_provider():
    result = generate_feature(FakeProvider(), "Search API", "Users can search products")
    assert result.startswith("Feature: Search API")
