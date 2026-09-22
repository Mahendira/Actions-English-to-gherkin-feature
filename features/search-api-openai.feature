Feature: Search API

  Scenario: Successful search query across multiple repositories
    Given the user is authenticated with a valid token
    And the user has access to the repositories
    When the user performs a search query with valid parameters
    Then the system returns a 200 OK response
    And the response contains a list of matching images
    And the response includes metadata for each image
    And the response includes pagination details

  Scenario: Search query with no results found
    Given the user is authenticated with a valid token
    And the user has access to the repositories
    When the user performs a search query that matches no images
    Then the system returns a 204 No Content response

  Scenario: Search query with invalid parameters
    Given the user is authenticated with a valid token
    When the user performs a search query with invalid parameters
    Then the system returns a 400 Bad Request response
    And the response includes an error message indicating the issue

  Scenario: Unauthorized access to a repository
    Given the user is authenticated with a valid token
    And the user does not have access to the requested repository
    When the user performs a search query on that repository
    Then the system returns a 403 Forbidden response

  Scenario: Repository not found
    Given the user is authenticated with a valid token
    When the user performs a search query on a non-existent repository
    Then the system returns a 404 Not Found response

  Scenario: Search query times out
    Given the user is authenticated with a valid token
    When the user performs a search query that exceeds the timeout limit
    Then the system returns a 504 Gateway Timeout response

  Scenario: Missing metadata fields in search results
    Given the user is authenticated with a valid token
    And the user has access to the repositories
    When the user performs a search query
    And some images have missing metadata fields
    Then the system returns a 200 OK response
    And the response includes images with available metadata only

  Scenario: Rate limit exceeded
    Given the user is authenticated with a valid token
    When the user exceeds the allowed number of search requests
    Then the system returns a 429 Too Many Requests response
    And the response includes an error message indicating the rate limit status
