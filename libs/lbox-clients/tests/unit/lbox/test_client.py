from unittest.mock import MagicMock

from lbox.request_client import RequestClient


# @patch.dict(os.environ, {'LABELBOX_API_KEY': 'bar'})
def test_headers():
    client = RequestClient(
        sdk_version="foo", api_key="api_key", endpoint="http://localhost:8080/_gql"
    )
    assert client.headers
    assert client.headers["Authorization"] == "Bearer api_key"
    assert client.headers["Content-Type"] == "application/json"
    assert client.headers["User-Agent"]
    assert client.headers["X-Python-Version"]


def test_custom_error_handling():
    mock_raise_error = MagicMock()

    response_dict = {
        "errors": [
            {
                "message": "Internal server error",
                "extensions": {"code": "INTERNAL_SERVER_ERROR"},
            }
        ],
    }
    response = MagicMock()
    response.json.return_value = response_dict
    response.status_code = 200

    client = RequestClient(
        sdk_version="foo", api_key="api_key", endpoint="http://localhost:8080/_gql"
    )
    connection_mock = MagicMock()
    connection_mock.send.return_value = response
    client._connection = connection_mock

    client.execute(
        "query_str",
        {"projectId": "project_id"},
        raise_return_resource_not_found=True,
        error_handlers={"INTERNAL_SERVER_ERROR": mock_raise_error},
    )
    mock_raise_error.assert_called_once_with(response)
