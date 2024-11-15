from unittest.mock import ANY, patch

from labelbox.client import Client


# @patch.dict(os.environ, {'LABELBOX_API_KEY': 'bar'})
def test_headers():
    client = Client(api_key="api_key", endpoint="http://localhost:8080/_gql")
    assert client.headers
    assert client.headers["Authorization"] == "Bearer api_key"
    assert client.headers["Content-Type"] == "application/json"
    assert client.headers["User-Agent"]
    assert client.headers["X-Python-Version"]


@patch('labelbox.client.RequestClient')
def test_client_initialization(mock_request_client):
    # Act: Initialize the Client
    client = Client(api_key='test_api_key')
    client.execute("query_str", {"projectId": "project_id"})

    # Assert: Check if the RequestClient was called with the correct arguments
    mock_request_client.return_value.execute.assert_called_once_with(
        ANY,
        ANY,
        data=ANY,
        files=ANY,
        timeout=ANY,
        experimental=False,
        error_log_key=ANY,
        raise_return_resource_not_found=ANY,
        error_handlers=ANY,
    )
    mock_request_client.reset_mock()

    client = Client(api_key='test_api_key', enable_experimental=True)
    client.execute("query_str", {"projectId": "project_id"})

    # Assert: Check if the RequestClient was called with the correct arguments
    mock_request_client.return_value.execute.assert_called_once_with(
        ANY,
        ANY,
        data=ANY,
        files=ANY,
        timeout=ANY,
        experimental=True,
        error_log_key=ANY,
        raise_return_resource_not_found=ANY,
        error_handlers=ANY,
    )
    mock_request_client.reset_mock()

    client = Client(api_key='test_api_key')
    client.enable_experimental = True
    client.execute("query_str", {"projectId": "project_id"})

    # Assert: Check if the RequestClient was called with the correct arguments
    mock_request_client.return_value.execute.assert_called_once_with(
        ANY,
        ANY,
        data=ANY,
        files=ANY,
        timeout=ANY,
        experimental=True,
        error_log_key=ANY,
        raise_return_resource_not_found=ANY,
        error_handlers=ANY,
    )
    mock_request_client.reset_mock()
    client = Client(api_key='test_api_key')
    client.enable_experimental = True
    client.execute("query_str", {"projectId": "project_id"}, experimental=False)

    # Assert: Check if the RequestClient was called with the correct arguments
    mock_request_client.return_value.execute.assert_called_once_with(
        ANY,
        ANY,
        data=ANY,
        files=ANY,
        timeout=ANY,
        experimental=True,
        error_log_key=ANY,
        raise_return_resource_not_found=ANY,
        error_handlers=ANY,
    )
