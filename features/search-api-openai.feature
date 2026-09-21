Feature: Search API

  Scenario: Successful search query across multiple repositories
    Given the user is authenticated with a valid token
    And the user has access to the repositories
    When the user performs a search query with valid parameters
    Then the system returns a 200 OK response
    And the response contains a list of matching images
    And the response includes metadata for each image
    And the response includes pagination details
    And the response includes repository source information

  Scenario: Search query returns no results
    Given the user is authenticated with a valid token
    And the user has access to the repositories
    When the user performs a search query with valid parameters that match no images
    Then the system returns a 204 No Content response

  Scenario: Search query with invalid parameters
    Given the user is authenticated with a valid token
    When the user performs a search query with invalid parameters
    Then the system returns a 400 Bad Request response
    And the response includes an error message indicating the issue

  Scenario: User is unauthorized to access a repository
    Given the user is authenticated with a valid token
    And the user does not have access to the requested repository
    When the user performs a search query on that repository
    Then the system returns a 403 Forbidden response
    And the response includes an error message indicating authorization failure

  Scenario: Search query times out
    Given the user is authenticated with a valid token
    And the user has access to the repositories
    When the user performs a search query that exceeds the timeout limit
    Then the system returns a 504 Gateway Timeout response
    And the response includes an error message indicating the timeout

  Scenario: Search query with missing metadata fields
    Given the user is authenticated with a valid token
    And the user has access to the repositories
    When the user performs a search query where some metadata fields are missing
    Then the system handles the missing fields gracefully
    And the system returns a 200 OK response with available results

  Scenario: Search query with unsupported file formats
    Given the user is authenticated with a valid token
    And the user has access to the repositories
    When the user performs a search query that includes unsupported file formats
    Then the system returns a 400 Bad Request response
    And the response includes an error message indicating unsupported formats
