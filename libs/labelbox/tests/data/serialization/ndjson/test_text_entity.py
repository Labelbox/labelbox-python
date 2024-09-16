import json

from labelbox.data.annotation_types.data.generic_data_row_data import (
    GenericDataRowData,
)
from labelbox.data.mixins import CustomMetric

from labelbox.data.serialization.ndjson.converter import NDJsonConverter
from labelbox.types import Label, ObjectAnnotation, TextEntity


def test_text_entity_import():
    with open("tests/data/assets/ndjson/text_entity_import.json", "r") as file:
        data = json.load(file)

    labels = [
        Label(
            data=GenericDataRowData(
                uid="cl6xnv9h61fv0085yhtoq06ht",
            ),
            annotations=[
                ObjectAnnotation(
                    custom_metrics=[
                        CustomMetric(name="customMetric1", value=0.5),
                        CustomMetric(name="customMetric2", value=0.3),
                    ],
                    confidence=0.53,
                    name="some-text-entity",
                    feature_schema_id="cl6xnuwt95lqq07330tbb3mfd",
                    extra={
                        "uuid": "5ad9c52f-058d-49c8-a749-3f20b84f8cd4",
                    },
                    value=TextEntity(start=67, end=128, extra={}),
                )
            ],
        )
    ]
    res = list(NDJsonConverter.serialize(labels))
    assert res == data


def test_text_entity_import_without_confidence():
    with open(
        "tests/data/assets/ndjson/text_entity_without_confidence_import.json",
        "r",
    ) as file:
        data = json.load(file)

    labels = [
        Label(
            data=GenericDataRowData(
                uid="cl6xnv9h61fv0085yhtoq06ht",
            ),
            annotations=[
                ObjectAnnotation(
                    name="some-text-entity",
                    feature_schema_id="cl6xnuwt95lqq07330tbb3mfd",
                    extra={
                        "uuid": "5ad9c52f-058d-49c8-a749-3f20b84f8cd4",
                    },
                    value=TextEntity(start=67, end=128, extra={}),
                )
            ],
        )
    ]

    res = list(NDJsonConverter.serialize(labels))
    assert res == data
