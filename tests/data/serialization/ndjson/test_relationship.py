import json
import pytest
from uuid import uuid4

from labelbox.data.serialization.ndjson.converter import NDJsonConverter


def test_relationship():
    with open('tests/data/assets/ndjson/relationship_import.json', 'r') as file:
        data = json.load(file)

    res = list(NDJsonConverter.deserialize(data))
    res = list(NDJsonConverter.serialize(res))

    assert res == data


def test_relationship_nonexistent_object():
    with open('tests/data/assets/ndjson/relationship_import.json', 'r') as file:
        data = json.load(file)

    relationship_annotation = data[2]
    source_uuid = relationship_annotation["relationship"]["source"]
    target_uuid = str(uuid4())
    relationship_annotation["relationship"]["target"] = target_uuid
    error_msg = f"Relationship object refers to nonexistent object with UUID '{source_uuid}' and/or '{target_uuid}'"

    with pytest.raises(ValueError, match=error_msg):
        list(NDJsonConverter.deserialize(data))


def test_relationship_duplicate_uuids():
    with open('tests/data/assets/ndjson/relationship_import.json', 'r') as file:
        data = json.load(file)

    source, target = data[0], data[1]
    target["uuid"] = source["uuid"]
    error_msg = f"UUID '{source['uuid']}' is not unique"

    with pytest.raises(AssertionError, match=error_msg):
        list(NDJsonConverter.deserialize(data))
