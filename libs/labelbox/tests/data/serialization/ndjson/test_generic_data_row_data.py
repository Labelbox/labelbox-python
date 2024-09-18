from labelbox.data.annotation_types.data.generic_data_row_data import (
    GenericDataRowData,
)
from labelbox.data.serialization.ndjson.converter import NDJsonConverter
from labelbox.types import Label, ClassificationAnnotation, Text


def test_generic_data_row_global_key():
    label_1 = Label(
        data=GenericDataRowData(global_key="test"),
        annotations=[
            ClassificationAnnotation(
                name="free_text",
                value=Text(answer="sample text"),
                extra={"uuid": "141c3592-e5f0-4866-9943-d4a21fd47eb0"},
            )
        ],
    )
    label_2 = Label(
        data={"global_key": "test"},
        annotations=[
            ClassificationAnnotation(
                name="free_text",
                value=Text(answer="sample text"),
                extra={"uuid": "141c3592-e5f0-4866-9943-d4a21fd47eb0"},
            )
        ],
    )

    expected_result = [
        {
            "answer": "sample text",
            "dataRow": {"globalKey": "test"},
            "name": "free_text",
            "uuid": "141c3592-e5f0-4866-9943-d4a21fd47eb0",
        }
    ]
    assert (
        list(NDJsonConverter.serialize([label_1]))
        == list(NDJsonConverter.serialize([label_2]))
        == expected_result
    )


def test_generic_data_row_id():
    label_1 = Label(
        data=GenericDataRowData(uid="test"),
        annotations=[
            ClassificationAnnotation(
                name="free_text",
                value=Text(answer="sample text"),
                extra={"uuid": "141c3592-e5f0-4866-9943-d4a21fd47eb0"},
            )
        ],
    )
    label_2 = Label(
        data={"uid": "test"},
        annotations=[
            ClassificationAnnotation(
                name="free_text",
                value=Text(answer="sample text"),
                extra={"uuid": "141c3592-e5f0-4866-9943-d4a21fd47eb0"},
            )
        ],
    )

    expected_result = [
        {
            "answer": "sample text",
            "dataRow": {"id": "test"},
            "name": "free_text",
            "uuid": "141c3592-e5f0-4866-9943-d4a21fd47eb0",
        }
    ]
    assert (
        list(NDJsonConverter.serialize([label_1]))
        == list(NDJsonConverter.serialize([label_2]))
        == expected_result
    )
