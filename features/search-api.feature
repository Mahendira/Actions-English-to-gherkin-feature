Feature: Search API

  Scenario: Successful search returns results
    Given the user is authenticated
    And the user has access to the search API
    When the user sends a search request with valid parameters
    Then the response status code should be 200
    And the response should contain a list of search results
    And the search results should match the search criteria

  Scenario: Search with invalid parameters returns an error
    Given the user is authenticated
    And the user has access to the search API
    When the user sends a search request with invalid parameters
    Then the response status code should be 400
    And the response should contain an error message indicating invalid parameters

  Scenario: Unauthenticated user attempts to search
    Given the user is not authenticated
    When the user sends a search request
    Then the response status code should be 401
    And the response should contain an error message indicating authentication is required
