import json

from labelbox.data.serialization.ndjson.converter import NDJsonConverter


def test_classification():
    with open(
        "tests/data/assets/ndjson/classification_import.json", "r"
    ) as file:
        data = json.load(file)
    res = list(NDJsonConverter.deserialize(data))
    res = list(NDJsonConverter.serialize(res))
    assert res == data


def test_classification_with_name():
    with open(
        "tests/data/assets/ndjson/classification_import_name_only.json", "r"
    ) as file:
        data = json.load(file)
    res = list(NDJsonConverter.deserialize(data))
    res = list(NDJsonConverter.serialize(res))
    assert res == data
