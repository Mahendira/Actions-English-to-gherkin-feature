from english_to_gherkin.consolidate import consolidate_feature
from english_to_gherkin.providers.base import LlmProvider

CANDIDATE = """Feature: Search
  Scenario: Search succeeds
    Given searchable images exist
    When the user searches
    Then matching images are returned
"""


class RepairingReviewer(LlmProvider):
    def __init__(self):
        self.calls = 0

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        self.calls += 1
        assert "source of truth" in system_prompt
        assert "Authoritative original requirement" in user_prompt
        if self.calls == 1:
            return """Feature: Search
  Scenario: Search succeeds
    Given searchable images exist
    Then matching images are returned
"""
        assert "missing a When step" in user_prompt
        return CANDIDATE


def test_reviewer_repairs_invalid_consolidation():
    reviewer = RepairingReviewer()
    result = consolidate_feature(
        reviewer,
        "Search",
        "Users can search images",
        {"candidate.feature": CANDIDATE},
    )
    assert result == CANDIDATE
    assert reviewer.calls == 2
