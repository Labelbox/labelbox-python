import pytest
import requests


def test_file_upload(client, rand_gen, dataset):
    data = rand_gen(str)
    uri = client.upload_data(data.encode())
    data_row = dataset.create_data_row(row_data=uri)
    assert requests.get(data_row.row_data).text == data
