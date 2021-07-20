import json

from labelbox.data.serialization.ndjson.converter import NDJsonConverter


def test_text():
    with open('tests/data/assets/ndjson/text_import.json', 'r') as file:
        data = json.load(file)
    res = NDJsonConverter.deserialize(data)
    res.data = list(res.data)
    res = list(NDJsonConverter.serialize(res))
    assert res == data
