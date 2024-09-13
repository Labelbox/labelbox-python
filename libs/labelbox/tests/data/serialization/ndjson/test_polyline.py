import json
import pytest
from labelbox.data.serialization.ndjson.converter import NDJsonConverter


@pytest.mark.parametrize(
    "filename",
    [
        "tests/data/assets/ndjson/polyline_without_confidence_import.json",
        "tests/data/assets/ndjson/polyline_import.json",
    ],
)
def test_polyline_import(filename: str):
    with open(filename, "r") as file:
        data = json.load(file)
    res = list(NDJsonConverter.deserialize(data))
    res = list(NDJsonConverter.serialize(res))
    assert res == data
