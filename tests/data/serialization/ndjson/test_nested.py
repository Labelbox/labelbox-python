import json

from labelbox.data.serialization.ndjson.converter import NDJsonConverter


def test_nested():
    with open('tests/data/assets/ndjson/nested_import.json', 'r') as file:
        data = json.load(file)
    res = list(NDJsonConverter.deserialize(data))
    res = list(NDJsonConverter.serialize(res))
    assert res == data


def test_nested_name_only():
    with open('tests/data/assets/ndjson/nested_import_name_only.json',
              'r') as file:
        data = json.load(file)
    res = list(NDJsonConverter.deserialize(data))
    res = list(NDJsonConverter.serialize(res))
    assert res == data
