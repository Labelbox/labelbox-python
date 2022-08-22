import json

from labelbox.data.serialization.ndjson.converter import NDJsonConverter


def test_text():
    with open('tests/data/assets/ndjson/text_import.json', 'r') as file:
        data = json.load(file)
    res = NDJsonConverter.deserialize(data).as_list()
    res = list(NDJsonConverter.serialize(res))
    assert res == data


def test_text_name_only():
    with open('tests/data/assets/ndjson/text_import_name_only.json',
              'r') as file:
        data = json.load(file)
    res = NDJsonConverter.deserialize(data).as_list()
    res = list(NDJsonConverter.serialize(res))
    assert res == data
