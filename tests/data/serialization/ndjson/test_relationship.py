import json
from uuid import uuid4

import pytest

from labelbox.data.serialization.ndjson.converter import NDJsonConverter


def test_relationship():
    with open("tests/data/assets/ndjson/relationship_import.json", "r") as file:
        data = json.load(file)

    res = list(NDJsonConverter.deserialize(data))
    res = list(NDJsonConverter.serialize(res))
    assert len(res) == len(data)

    res_relationship_annotation, res_relationship_second_annotation = [
        annot for annot in res if "relationship" in annot
    ]
    res_source_and_target = [
        annot for annot in res if "relationship" not in annot
    ]
    assert res_relationship_annotation

    assert res_relationship_annotation["relationship"]["source"] in [
        annot["uuid"] for annot in res_source_and_target
    ]
    assert res_relationship_annotation["relationship"]["target"] in [
        annot["uuid"] for annot in res_source_and_target
    ]

    assert res_relationship_second_annotation
    assert res_relationship_second_annotation["relationship"][
        "source"] != res_relationship_annotation["relationship"]["source"]
    assert res_relationship_second_annotation["relationship"][
        "target"] != res_relationship_annotation["relationship"]["target"]
    assert res_relationship_second_annotation["relationship"]["source"] in [
        annot["uuid"] for annot in res_source_and_target
    ]
    assert res_relationship_second_annotation["relationship"]["target"] in [
        annot["uuid"] for annot in res_source_and_target
    ]


def test_relationship_nonexistent_object():
    with open("tests/data/assets/ndjson/relationship_import.json", "r") as file:
        data = json.load(file)

    relationship_annotation = data[2]
    source_uuid = relationship_annotation["relationship"]["source"]
    target_uuid = str(uuid4())
    relationship_annotation["relationship"]["target"] = target_uuid
    error_msg = f"Relationship object refers to nonexistent object with UUID '{source_uuid}' and/or '{target_uuid}'"

    with pytest.raises(ValueError, match=error_msg):
        list(NDJsonConverter.deserialize(data))


def test_relationship_duplicate_uuids():
    with open("tests/data/assets/ndjson/relationship_import.json", "r") as file:
        data = json.load(file)

    source, target = data[0], data[1]
    target["uuid"] = source["uuid"]
    error_msg = f"UUID '{source['uuid']}' is not unique"

    with pytest.raises(AssertionError, match=error_msg):
        list(NDJsonConverter.deserialize(data))
