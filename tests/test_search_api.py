import pytest
from unittest.mock import patch

@pytest.fixture
def valid_token():
    return "valid_token"

@pytest.fixture
def authorized_user():
    return "authorized_user"

@pytest.fixture
def search_response():
    return {
        "images": [
            {"file_name": "sunset.jpg", "upload_date": "2023-01-01", "file_type": "image", "metadata": {"project": "vacation"}}
        ],
        "pagination": {"limit": 2, "offset": 0, "total": 1}
    }

@pytest.mark.parametrize(
    'query, expected_status',
    [
        ("sunset", 200),
        ("nonexistent", 204)
    ]
)
@patch('search_api.search')
def test_successful_search(query, expected_status, search_response, valid_token, authorized_user, mock_search):
    mock_search.return_value = search_response if expected_status == 200 else None
    response = search_api.search(valid_token, authorized_user, query)
    assert response.status_code == expected_status

@pytest.mark.parametrize(
    'query_specification, expected_result',
    [
        ("partial match on file name for 'sunset'", "file name contains 'sunset'"),
        ("exact match on file name for 'sunset.jpg'", "file name equals 'sunset.jpg'"),
    ]
)
@patch('search_api.search')
def test_metadata_matching_modes(query_specification, expected_result, valid_token, authorized_user, search_response, mock_search):
    mock_search.return_value = search_response
    response = search_api.search(valid_token, authorized_user, query_specification)
    assert response.status_code == 200
    assert any(expected_result in img['file_name'] for img in response.images)

@pytest.mark.parametrize(
    'limit, offset, expected_count',
    [(2, 0, 2), (2, 1, 1)]
)
@patch('search_api.search')
def test_pagination_controls(limit, offset, expected_count, valid_token, authorized_user, search_response, mock_search):
    mock_search.return_value = search_response
    response = search_api.search(valid_token, authorized_user, "sunset", limit=limit, offset=offset)
    assert response.status_code == 200
    assert len(response.images) <= expected_count

@pytest.mark.parametrize(
    'auth_state, error_condition, expected_status',
    [
        ("no authentication token", "missing authentication token", 401),
        ("an invalid OAuth2/JWT token", "invalid authentication token", 401),
    ]
)
@patch('search_api.search')
def test_standardized_error_responses(auth_state, error_condition, expected_status, mock_search):
    mock_search.side_effect = Exception(error_condition)
    response = search_api.search(auth_state)
    assert response.status_code == expected_status
    assert "errorCode" in response.json()
    assert "errorMessage" in response.json()
