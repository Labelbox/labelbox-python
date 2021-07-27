import json

from labelbox.data.serialization.ndjson.converter import NDJsonConverter


def test_nested():
    with open('tests/data/assets/ndjson/nested_import.json', 'r') as file:
        data = json.load(file)
    res = NDJsonConverter.deserialize(data).as_list()
    res = list(NDJsonConverter.serialize(res))
    assert res == data
