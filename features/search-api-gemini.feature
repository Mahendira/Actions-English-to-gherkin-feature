Feature: Unified Image Search API

  Background:
    Given the search API is available
    And the system is connected to image repositories containing normalized metadata

  Scenario: Perform a successful search with filters and pagination
    Given the user has a valid authentication token and access to the internal repository
    When the user sends a search request for query "nature" with file type "jpg" and limit 10
    Then the system should respond with status 200
    And the response should contain a list of matching images
    And the response should include metadata, pagination details, and repository source information

  Scenario: Execute a search that yields no results
    Given the user has a valid authentication token
    When the user sends a search request for query "nonexistentimagexyz"
    Then the system should respond with status 204

  Scenario Outline: Handle client error responses for invalid search requests
    Given the user has a valid authentication token
    When the user sends a search request with invalid parameters "<Query>" and filters "<Filters>"
    Then the system should respond with status <StatusCode>
    And the response should contain a JSON error message with errorCode and errorMessage

    Examples:
      | Query | Filters | StatusCode |
      |       | invalid_filter_syntax | 400 |
      | test  | conflicting_parameters | 409 |

  Scenario: Reject unauthenticated search requests
    Given the user has no authentication token
    When the user sends a search request for query "test"
    Then the system should respond with status 401

  Scenario: Restrict search results based on user authorization
    Given the user has an authentication token but lacks access to the Box repository
    When the user sends a search request for query "logo"
    Then the system should respond with status 200
    And the results should not include images from the Box repository

  Scenario: Handle upstream repository connection failure
    Given the user has a valid authentication token
    And an upstream repository is temporarily unavailable
    When the user sends a search request covering all repositories
    Then the system should respond with status 503
    And the response should contain a JSON error message describing the failure
