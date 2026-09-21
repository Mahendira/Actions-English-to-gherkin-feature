Feature: Search API

Scenario: Successful search with filters
Given a valid authentication token for user "alice"
And the system has indexed images from repository "internal" with metadata
When the user performs a search request to "/api/search" with query "sunset", filter "fileName" contains "sunset", limit 10, offset 0, sort "uploadDate asc"
Then the response status code is 200 OK
And the response body contains a list of matching images
And each image includes metadata, repository source info, and pagination details
And the total result count is returned
And the response time is less than 2 seconds
And the system logs the request with user ID, timestamp, query parameters, result count

Scenario: Search returns no results
Given a valid authentication token for user "bob"
When the user performs a search request to "/api/search" with query "nonexistentimage", no filters, limit 5, offset 0
Then the response status code is 204 No Content
And the response body is empty
And pagination details indicate zero results
And the system logs the request with user ID, timestamp, query parameters, result count

Scenario: Unauthorized access (missing token)
Given no authentication token
When the user performs a search request to "/api/search" with query "test"
Then the response status code is 401 Unauthorized
And the error response includes errorCode "UNAUTHORIZED", errorMessage "Missing or invalid authentication token"

Scenario: Forbidden due to insufficient permissions
Given a valid authentication token for user "charlie" who lacks access to repository "box"
When the user performs a search request to "/api/search" with query "doc", filter "repository" equals "box"
Then the response status code is 403 Forbidden
And the error response includes errorCode "FORBIDDEN", errorMessage "User not authorized to access requested repository"

Scenario: Bad request due to invalid filter
Given a valid authentication token for user "dave"
When the user performs a search request to "/api/search" with query "image", filter "invalidField" equals "value"
Then the response status code is 400 Bad Request
And the error response includes errorCode "BAD_REQUEST", errorMessage "Invalid query parameters or unsupported metadata fields"

Scenario: Not found repository
Given a valid authentication token for user "eve"
When the user performs a search request to "/api/search" with filter "repository" equals "nonexistentRepo"
Then the response status code is 404 Not Found
And the error response includes errorCode "NOT_FOUND", errorMessage "Repository not found"

Scenario: Conflict due to incompatible filter combination
Given a valid authentication token for user "frank"
When the user performs a search request to "/api/search" with both "fileName" exact match and "fileName" contains filter
Then the response status code is 409 Conflict
And the error response includes errorCode "CONFLICT", errorMessage "Conflicting query parameters or incompatible filter combinations"

Scenario: External provider error (502 Bad Gateway)
Given a valid authentication token for user "grace"
When the user performs a search request to "/api/search" with query "data"
Then the response status code is 502 Bad Gateway
And the error response includes errorCode "BAD_GATEWAY", errorMessage "Upstream repository returned an invalid response"

Scenario: Missing metadata handling
Given a valid authentication token for user "heidi"
And the system has indexed an image with missing "tags" metadata
When the user performs a search request to "/api/search" with filter "tags" contains "vacation"
Then the response status code is 200 OK
And the result list does not contain the image (since tags missing)
And the system logs the missing metadata event

Scenario: Rate limit handling (503 Service Unavailable)
Given a valid authentication token for user "ivan"
When the user performs a search request to "/api/search" with query "report"
Then the response status code is 503 Service Unavailable
And the error response includes errorCode "SERVICE_UNAVAILABLE", errorMessage "Repository temporarily unavailable due to rate limiting"
