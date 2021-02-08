import pytest
import requests


# TODO it seems that at some point Google Storage (gs prefix) started being
# returned, and we can't just download those with requests. Fix this
@pytest.mark.skip
def test_file_upload(client, rand_gen):
    data = rand_gen(str)
    url = client.upload_data(data.encode())
    assert requests.get(url).text == data
