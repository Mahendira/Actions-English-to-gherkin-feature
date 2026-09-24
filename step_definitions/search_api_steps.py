import pytest
from pytest_bdd import scenarios, given, when, then, parsers

scenarios('features/search_api.feature')

@given('the user has a valid OAuth2/JWT token')
def valid_token():
    pass

@given('the user is authorized to access two connected repositories')
def authorized_access():
    pass

@given('the system has extracted, stored, and indexed normalized metadata from all connected repositories')
def indexed_metadata():
    pass

@when('the user sends a search request to the unified search endpoint with a query, optional filters, limit, offset, and sort order')
def send_search_request():
    pass

@then('the system returns a 200 OK response')
def check_response_ok():
    pass

@then('the response contains a list of matching images')
def check_matching_images():
    pass

@then('each image includes metadata and repository source information')
def check_image_metadata():
    pass

@then('the response contains only images the user is authorized to access')
def check_authorized_images():
    pass

@then('the response includes pagination details')
def check_pagination_details():
    pass

@then('the results are sorted according to the requested sort order')
def check_sort_order():
    pass

@then('the response is returned within 2 seconds')
def check_response_time():
    pass

@then('the system logs the request with user ID, timestamp, query parameters, and result count')
def check_logging():
    pass

# Additional step definitions for other scenarios would follow the same pattern.
