Feature: search-api

  @performance @audit
  Scenario: Successful unified search with filters, pagination, and sorting
    Given the user has a valid OAuth2/JWT token
    And the user is authorized to access two connected repositories
    And the system has extracted, stored, and indexed normalized metadata from all connected repositories
    When the user sends a search request to the unified search endpoint with a query, optional filters, limit, offset, and sort order
    Then the system returns a 200 OK response
    And the response contains a list of matching images
    And each image includes metadata and repository source information
    And the response contains only images the user is authorized to access
    And the response includes pagination details
    And the results are sorted according to the requested sort order
    And the response is returned within 2 seconds
    And the system logs the request with user ID, timestamp, query parameters, and result count

  @audit
  Scenario: Search with no matching images
    Given the user has a valid OAuth2/JWT token
    And the user is authorized to access the connected repositories
    When the user sends a search request to the unified search endpoint that matches no images
    Then the system returns a 204 No Content response
    And the response has no content
    And the system logs the request with user ID, timestamp, query parameters, and result count zero

  @audit
  Scenario Outline: Support metadata matching modes
    Given the user has a valid OAuth2/JWT token
    And the user is authorized to access the connected repositories
    And the system has indexed images with metadata from all connected repositories that match the requested criteria
    When the user sends a search request with <query_specification>
    Then the system returns a 200 OK response
    And the response includes at least one image that satisfies <expected_result>
    And the system logs the request with user ID, timestamp, query parameters, and result count

    Examples:
      | query_specification | expected_result |
      | partial match on file name for "sunset" | file name contains "sunset" |
      | exact match on file name for "sunset.jpg" | file name equals "sunset.jpg" |
      | exact match on upload date for the requested upload date | upload date equals the requested upload date |
      | exact match on file type for "image" | file type equals "image" |
      | partial match on a custom metadata field for "project" | the custom metadata field contains "project" |
      | multi-criteria query with file type "image" and tags "vacation" | file type equals "image" and tags include "vacation" |

  @performance @audit
  Scenario: Pagination controls limit, offset, and sort order for high-volume queries
    Given the user has a valid OAuth2/JWT token
    And the user is authorized to access the connected repositories
    And the system has indexed a high volume of metadata from all connected repositories
    When the user sends a search request with limit 2, offset 0, and sort order by upload date ascending
    Then the system returns a 200 OK response
    And the response contains at most 2 matching images
    And the response includes pagination details
    And the images are sorted by upload date ascending
    And the response is returned within 2 seconds
    And the system logs the request with user ID, timestamp, query parameters, and result count

  @audit
  Scenario: Metadata is normalized across connected repositories
    Given the system has extracted, stored, and indexed metadata from all connected repositories
    And the user has a valid OAuth2/JWT token
    And the user is authorized to access two connected repositories
    When the user sends a search request using a normalized metadata field
    Then the system returns a 200 OK response
    And the same normalized metadata field is used consistently in the filters and results for both repositories
    And the system logs the request with user ID, timestamp, query parameters, and result count

  @audit
  Scenario: Missing, malformed, or incomplete metadata is handled gracefully
    Given the user has a valid OAuth2/JWT token
    And the user is authorized to access the connected repositories
    And some indexed images have missing, malformed, or incomplete metadata fields
    When the user sends a search request to the unified search endpoint
    Then the system returns a 200 OK response
    And the response does not include malformed metadata values
    And the search does not fail because of the missing, malformed, or incomplete metadata
    And the system logs the request with user ID, timestamp, query parameters, and result count

  @audit
  Scenario: Unsupported file formats are handled gracefully
    Given the user has a valid OAuth2/JWT token
    And the user is authorized to access the connected repositories
    And an indexed image has an unsupported file format
    When the user sends a search request to the unified search endpoint
    Then the system returns a 200 OK response
    And the search does not fail because of the unsupported file format
    And the system logs the request with user ID, timestamp, query parameters, and result count

  @security @audit
  Scenario: File-level authorization restricts results
    Given the user has a valid OAuth2/JWT token
    And the user is authorized to access a repository but not every file in it
    And the repository contains at least one image the user is authorized to access
    When the user sends a search request to the unified search endpoint
    Then the system returns a 200 OK response
    And the response contains only images the user is authorized to access
    And the system logs the request with user ID, timestamp, query parameters, and result count

  @security @audit
  Scenario: Sensitive metadata is masked or excluded
    Given the user has a valid OAuth2/JWT token
    And the user is not authorized to view a sensitive metadata field
    And the repository contains at least one image with that sensitive metadata field
    When the user sends a search request that returns an image with that sensitive metadata field
    Then the system returns a 200 OK response
    And the sensitive metadata field is masked or excluded from the response
    And the system logs the request with user ID, timestamp, query parameters, and result count

  @security @audit
  Scenario Outline: Return standardized error responses
    Given the user has <auth_state>
    When the user sends a search request that triggers <error_condition>
    Then the system returns a <status_code> response
    And the response body is JSON containing errorCode and a clear, descriptive errorMessage
    And the system logs the error with full diagnostic details excluding sensitive data

    Examples:
      | auth_state | error_condition | status_code |
      | no authentication token | missing authentication token | 401 |
      | an invalid OAuth2/JWT token | invalid authentication token | 401 |
      | a valid OAuth2/JWT token | invalid query parameters, malformed filters, or unsupported metadata fields | 400 |
      | a valid OAuth2/JWT token | user is not authorized to access the requested repository or metadata | 403 |
      | a valid OAuth2/JWT token | repository or resource not found | 404 |
      | a valid OAuth2/JWT token | conflicting query parameters or incompatible filter combinations | 409 |
      | a valid OAuth2/JWT token | unexpected server failure | 500 |
      | a valid OAuth2/JWT token | upstream repository returned an invalid response | 502 |
      | a valid OAuth2/JWT token | repository temporarily unavailable | 503 |
      | a valid OAuth2/JWT token | external repository returns a rate-limit response | 503 |
      | a valid OAuth2/JWT token | search request timed out due to slow external provider | 504 |
