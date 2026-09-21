import pytest

from english_to_gherkin.errors import ValidationError
from english_to_gherkin.gherkin import clean_generated_text, validate_gherkin


def test_removes_markdown_fence_and_preamble():
    raw = "Explanation\n```gherkin\nFeature: Search\n  Scenario: Find item\n    Given an item exists\n    When I search\n    Then I see the item\n```"
    cleaned = clean_generated_text(raw)
    assert cleaned.startswith("Feature: Search")
    assert "```" not in cleaned


def test_accepts_multiple_complete_scenarios():
    text = """Feature: Search
  Scenario: Find item
    Given an item exists
    When I search
    Then I see the item

  Scenario: No result
    Given no matching item exists
    When I search
    Then I see no results
"""
    validate_gherkin(text)


def test_rejects_scenario_without_then():
    text = """Feature: Search
  Scenario: Find item
    Given an item exists
    When I search
"""
    with pytest.raises(ValidationError, match="missing a Then"):
        validate_gherkin(text)
