from lbox.request_client import RequestClient


# @patch.dict(os.environ, {'LABELBOX_API_KEY': 'bar'})
def test_headers():
    client = RequestClient(sdk_version="foo", api_key="api_key", endpoint="http://localhost:8080/_gql")
    assert client.headers
    assert client.headers["Authorization"] == "Bearer api_key"
    assert client.headers["Content-Type"] == "application/json"
    assert client.headers["User-Agent"]
    assert client.headers["X-Python-Version"]
