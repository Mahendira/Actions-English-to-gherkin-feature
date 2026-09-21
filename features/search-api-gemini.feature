Feature: Search API
  As an API consumer
  I want to search across multiple image repositories using a unified endpoint
  So that I can find authorized images based on flexible queries and metadata filters

  Background:
    Given the search API is available

  Scenario: Successfully search for images with valid parameters
    Given the user is authenticated with a valid token
    When the user sends a search request with query "nature", limit "10", and offset "0"
    Then the system should return a 200 OK response
    And the response should contain a list of matching images with metadata, pagination details, and repository source information
    And only images the user is authorized to access should be returned

  Scenario: Execute a search that yields no matching results
    Given the user is authenticated with a valid token
    When the user sends a search request for a query that does not exist
    Then the system should return a 204 No Content response

  Scenario Outline: Reject search requests with invalid parameters or combinations
    Given the user is authenticated with a valid token
    When the user sends a search request with <condition>
    Then the system should return a <status_code> response
    And the response should contain a JSON error message with errorCode and errorMessage

    Examples:
      | condition                                    | status_code |
      | invalid query parameters or malformed filters | 400         |
      | conflicting query parameters                 | 409         |

  Scenario: Reject unauthenticated search requests
    Given the user is unauthenticated
    When the user sends a search request
    Then the system should return a 401 Unauthorized response

  Scenario: Restrict search when user lacks authorization for repository
    Given the user is authenticated with a valid token
    When the user sends a search request targeting a repository they cannot access
    Then the system should return a 403 Forbidden response
