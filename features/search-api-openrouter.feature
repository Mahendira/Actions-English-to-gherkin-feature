Feature: Search API

Scenario: Successful search with results
Given a user with a valid authentication token
And the system has indexed images from repositories with metadata
When the user performs a search query with optional filters (e.g., file name containing "cat", tags "nature")
Then the API returns HTTP 200 OK
And the response includes a list of matching images with metadata, pagination details, and repository source information

Scenario: Search returns no results
Given a user with a valid authentication token
And the system has no images matching the query criteria
When the user performs a search query with exact match "nonexistentfile.jpg"
Then the API returns HTTP 204 No Content
And the response body is empty

Scenario: Invalid query parameters
Given a user with a valid authentication token
When the user performs a search with an unsupported metadata field "invalidfield"
Then the API returns HTTP 400 Bad Request
And the error response includes errorCode "INVALID_PARAMETER", errorMessage "Invalid query parameters", details "Unsupported metadata field"

Scenario: Missing authentication
Given a user without an authentication token
When the user attempts to perform a search
Then the API returns HTTP 401 Unauthorized
And the error response includes errorCode "UNAUTHORIZED", errorMessage "Missing or invalid authentication token"

Scenario: Insufficient authorization
Given a user with a valid authentication token but no access to repository "box"
When the user performs a search filtering by repository "box"
Then the API returns HTTP 403 Forbidden
And the error response includes errorCode "FORBIDDEN", errorMessage "User not authorized to access requested repository"

Scenario: Repository not found
Given a user with a valid authentication token
When the user performs a search with repository "nonexistentrepo"
Then the API returns HTTP 404 Not Found
And the error response includes errorCode "NOT_FOUND", errorMessage "Repository not found"

Scenario: Conflicting query parameters
Given a user with a valid authentication token
When the user performs a search with both exact match and partial match on the same field
Then the API returns HTTP 409 Conflict
And the error response includes errorCode "CONFLICT", errorMessage "Conflicting query parameters"

Scenario: Upstream repository error (502)
Given a user with a valid authentication token
And the external repository (Box) returns an invalid response
When the user performs a search
Then the API returns HTTP 502 Bad Gateway
And the error response includes errorCode "BAD_GATEWAY", errorMessage "Upstream repository returned an invalid response"

Scenario: Service unavailable (503)
Given a user with a valid authentication token
And the repository service is temporarily unavailable
When the user performs a search
Then the API returns HTTP 503 Service Unavailable
And the error response includes errorCode "SERVICE_UNAVAILABLE", errorMessage "Repository temporarily unavailable"

Scenario: Gateway timeout (504)
Given a user with a valid authentication token
And the repository response times out
When the user performs a search
Then the API returns HTTP 504 Gateway Timeout
And the error response includes errorCode "GATEWAY_TIMEOUT", errorMessage "Search request timed out due to slow external provider"

Scenario: Metadata handling missing fields
Given a user with a valid authentication token
And an image with missing metadata fields is indexed
When the user searches for that image using a missing field
Then the API returns HTTP 200 OK
And the response includes the image with null or default values for missing fields

Scenario: Pagination controls
Given a user with a valid authentication token
And 25 indexed images matching the query
When the user performs a search with limit=10 offset=0
Then the API returns HTTP 200 OK
And the response includes the first 10 images
And pagination details indicate total count 25, limit 10, offset 0
