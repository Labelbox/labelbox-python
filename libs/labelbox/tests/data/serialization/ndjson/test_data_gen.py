from copy import copy
import pytest
import labelbox.types as lb_types
from labelbox.data.serialization import NDJsonConverter
from labelbox.data.serialization.ndjson.objects import (
    NDDicomSegments,
    NDDicomSegment,
    NDDicomLine,
)

"""
Data gen prompt test data
"""

prompt_text_annotation = lb_types.PromptClassificationAnnotation(
    feature_schema_id="ckrb1sfkn099c0y910wbo0p1a",
    name="test",
    value=lb_types.PromptText(
        answer="the answer to the text questions right here"
    ),
)

prompt_text_ndjson = {
    "answer": "the answer to the text questions right here",
    "name": "test",
    "schemaId": "ckrb1sfkn099c0y910wbo0p1a",
    "dataRow": {"id": "ckrb1sf1i1g7i0ybcdc6oc8ct"},
}

data_gen_label = lb_types.Label(
    data={"uid": "ckrb1sf1i1g7i0ybcdc6oc8ct"},
    annotations=[prompt_text_annotation],
)

"""
Prompt annotation test
"""


def test_serialize_label():
    serialized_label = next(NDJsonConverter().serialize([data_gen_label]))
    # Remove uuid field since this is a random value that can not be specified also meant for relationships
    del serialized_label["uuid"]
    assert serialized_label == prompt_text_ndjson


def test_deserialize_label():
    deserialized_label = next(
        NDJsonConverter().deserialize([prompt_text_ndjson])
    )
    if hasattr(deserialized_label.annotations[0], "extra"):
        # Extra fields are added to deserialized label by default need removed to match
        deserialized_label.annotations[0].extra = {}
    assert deserialized_label.model_dump(
        exclude_none=True
    ) == data_gen_label.model_dump(exclude_none=True)


def test_serialize_deserialize_label():
    serialized = list(NDJsonConverter.serialize([data_gen_label]))
    deserialized = next(NDJsonConverter.deserialize(serialized))
    if hasattr(deserialized.annotations[0], "extra"):
        # Extra fields are added to deserialized label by default need removed to match
        deserialized.annotations[0].extra = {}
    assert deserialized.model_dump(
        exclude_none=True
    ) == data_gen_label.model_dump(exclude_none=True)
