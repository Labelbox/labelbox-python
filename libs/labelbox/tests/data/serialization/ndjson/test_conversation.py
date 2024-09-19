import json

from labelbox.data.annotation_types.data.generic_data_row_data import (
    GenericDataRowData,
)
import pytest
import labelbox.types as lb_types
from labelbox.data.serialization.ndjson.converter import NDJsonConverter
from labelbox.data.mixins import CustomMetric

radio_ndjson = [
    {
        "dataRow": {"globalKey": "my_global_key"},
        "name": "radio",
        "answer": {"name": "first_radio_answer"},
        "messageId": "0",
    }
]

radio_label = [
    lb_types.Label(
        data=lb_types.GenericDataRowData(global_key="my_global_key"),
        annotations=[
            lb_types.ClassificationAnnotation(
                name="radio",
                value=lb_types.Radio(
                    answer=lb_types.ClassificationAnswer(
                        name="first_radio_answer"
                    )
                ),
                message_id="0",
            )
        ],
    )
]

checklist_ndjson = [
    {
        "dataRow": {"globalKey": "my_global_key"},
        "name": "checklist",
        "answer": [
            {"name": "first_checklist_answer"},
            {"name": "second_checklist_answer"},
        ],
        "messageId": "2",
    }
]

checklist_label = [
    lb_types.Label(
        data=lb_types.GenericDataRowData(global_key="my_global_key"),
        annotations=[
            lb_types.ClassificationAnnotation(
                name="checklist",
                message_id="2",
                value=lb_types.Checklist(
                    answer=[
                        lb_types.ClassificationAnswer(
                            name="first_checklist_answer"
                        ),
                        lb_types.ClassificationAnswer(
                            name="second_checklist_answer"
                        ),
                    ]
                ),
            )
        ],
    )
]

free_text_ndjson = [
    {
        "dataRow": {"globalKey": "my_global_key"},
        "name": "free_text",
        "answer": "sample text",
        "messageId": "0",
    }
]
free_text_label = [
    lb_types.Label(
        data=lb_types.GenericDataRowData(global_key="my_global_key"),
        annotations=[
            lb_types.ClassificationAnnotation(
                name="free_text",
                message_id="0",
                value=lb_types.Text(answer="sample text"),
            )
        ],
    )
]


@pytest.mark.parametrize(
    "label, ndjson",
    [
        [radio_label, radio_ndjson],
        [checklist_label, checklist_ndjson],
        [free_text_label, free_text_ndjson],
    ],
)
def test_message_based_radio_classification(label, ndjson):
    serialized_label = list(NDJsonConverter().serialize(label))
    serialized_label[0].pop("uuid")
    assert serialized_label == ndjson


def test_conversation_entity_import():
    with open(
        "tests/data/assets/ndjson/conversation_entity_import.json", "r"
    ) as file:
        data = json.load(file)

    label = lb_types.Label(
        data=GenericDataRowData(
            uid="cl6xnv9h61fv0085yhtoq06ht",
        ),
        annotations=[
            lb_types.ObjectAnnotation(
                custom_metrics=[
                    CustomMetric(name="customMetric1", value=0.5),
                    CustomMetric(name="customMetric2", value=0.3),
                ],
                confidence=0.53,
                name="some-text-entity",
                feature_schema_id="cl6xnuwt95lqq07330tbb3mfd",
                extra={"uuid": "5ad9c52f-058d-49c8-a749-3f20b84f8cd4"},
                value=lb_types.ConversationEntity(
                    start=67, end=128, message_id="some-message-id"
                ),
            )
        ],
    )

    res = list(NDJsonConverter.serialize([label]))
    assert res == data


def test_conversation_entity_import_without_confidence():
    with open(
        "tests/data/assets/ndjson/conversation_entity_without_confidence_import.json",
        "r",
    ) as file:
        data = json.load(file)
    label = lb_types.Label(
        uid=None,
        data=GenericDataRowData(
            uid="cl6xnv9h61fv0085yhtoq06ht",
        ),
        annotations=[
            lb_types.ObjectAnnotation(
                name="some-text-entity",
                feature_schema_id="cl6xnuwt95lqq07330tbb3mfd",
                extra={"uuid": "5ad9c52f-058d-49c8-a749-3f20b84f8cd4"},
                value=lb_types.ConversationEntity(
                    start=67, end=128, extra={}, message_id="some-message-id"
                ),
            )
        ],
    )

    res = list(NDJsonConverter.serialize([label]))
    assert res == data


def test_benchmark_reference_label_flag_enabled():
    label = lb_types.Label(
        data=lb_types.GenericDataRowData(global_key="my_global_key"),
        annotations=[
            lb_types.ClassificationAnnotation(
                name="free_text",
                message_id="0",
                value=lb_types.Text(answer="sample text"),
            )
        ],
        is_benchmark_reference=True,
    )

    res = list(NDJsonConverter.serialize([label]))
    assert res[0]["isBenchmarkReferenceLabel"]


def test_benchmark_reference_label_flag_disabled():
    label = lb_types.Label(
        data=lb_types.GenericDataRowData(global_key="my_global_key"),
        annotations=[
            lb_types.ClassificationAnnotation(
                name="free_text",
                message_id="0",
                value=lb_types.Text(answer="sample text"),
            )
        ],
        is_benchmark_reference=False,
    )

    res = list(NDJsonConverter.serialize([label]))
    assert not res[0].get("isBenchmarkReferenceLabel")
