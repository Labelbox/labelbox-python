import json

import pytest

from labelbox.data.serialization.ndjson.converter import NDJsonConverter


@pytest.mark.parametrize(
    "filename",
    [
        "tests/data/assets/ndjson/text_entity_import.json",
        "tests/data/assets/ndjson/text_entity_without_confidence_import.json",
    ],
)
def test_text_entity_import(filename: str):
    with open(filename, "r") as file:
        data = json.load(file)

    res = list(NDJsonConverter.deserialize(data))
    res = list(NDJsonConverter.serialize(res))
    assert res == data
