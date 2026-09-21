Feature: Search API

  Scenario: Successful search returns results
    Given the user is authenticated
    When the user sends a search request with valid query parameters
    Then the API should return a 200 status code
    And the response should contain a list of search results
    And the search results should match the query parameters

  Scenario: Search with invalid query parameters
    Given the user is authenticated
    When the user sends a search request with invalid query parameters
    Then the API should return a 400 status code
    And the response should contain an error message indicating the invalid parameters

  Scenario: Unauthenticated user attempts to search
    Given the user is not authenticated
    When the user sends a search request
    Then the API should return a 401 status code
    And the response should contain an error message indicating authentication is required
