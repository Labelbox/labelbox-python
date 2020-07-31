import requests


def test_file_uplad(client, rand_gen):
    data = rand_gen(str)
    url = client.upload_data(data.encode())
    assert requests.get(url).text == data
