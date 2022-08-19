import json

from labelbox.data.serialization.ndjson.converter import NDJsonConverter

IGNORE_KEYS = ['unit', 'page']


def test_nested():
    with open('tests/data/assets/ndjson/nested_import.json', 'r') as file:
        data = json.load(file)
    res = NDJsonConverter.deserialize(data).as_list()
    res = list(NDJsonConverter.serialize(res))
    for r in res:
        for key in IGNORE_KEYS:
            r.pop(key, None)
    assert res == data


def test_nested_name_only():
    with open('tests/data/assets/ndjson/nested_import_name_only.json',
              'r') as file:
        data = json.load(file)
    res = NDJsonConverter.deserialize(data).as_list()
    res = list(NDJsonConverter.serialize(res))
    for r in res:
        for key in IGNORE_KEYS:
            r.pop(key, None)
    assert res == data
