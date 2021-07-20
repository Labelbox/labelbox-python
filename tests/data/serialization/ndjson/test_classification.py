import json

from labelbox.data.serialization.ndjson.converter import NDJsonConverter


def test_classification():
    with open('tests/data/assets/ndjson/classification_import.json', 'r') as file:
        data = json.load(file)
    res = NDJsonConverter.deserialize(data)
    res.data = list(res.data)
    res = list(NDJsonConverter.serialize(res))
    assert res == data
