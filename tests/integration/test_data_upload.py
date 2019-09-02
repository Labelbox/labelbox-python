import urllib.request

def test_file_uplad(client, rand_gen):
    data = rand_gen(str)
    url = client.upload_data(data.encode())
    retrieved = urllib.request.urlopen(url).read().decode()
    assert data == retrieved
