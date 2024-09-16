import json
from labelbox.data.annotation_types.data.generic_data_row_data import (
    GenericDataRowData,
)
from labelbox.data.mixins import CustomMetric
from labelbox.data.serialization.ndjson.converter import NDJsonConverter
from labelbox.types import ObjectAnnotation, Point, Line, Label


def test_polyline_import_with_confidence():
    with open(
        "tests/data/assets/ndjson/polyline_without_confidence_import.json", "r"
    ) as file:
        data = json.load(file)
    labels = [
        Label(
            data=GenericDataRowData(
                uid="cl6xnv9h61fv0085yhtoq06ht",
            ),
            annotations=[
                ObjectAnnotation(
                    name="some-line",
                    feature_schema_id="cl6xnuwt95lqq07330tbb3mfd",
                    extra={
                        "uuid": "5ad9c52f-058d-49c8-a749-3f20b84f8cd4",
                    },
                    value=Line(
                        points=[
                            Point(x=2534.353, y=249.471),
                            Point(x=2429.492, y=182.092),
                            Point(x=2294.322, y=221.962),
                        ],
                    ),
                )
            ],
        )
    ]
    res = list(NDJsonConverter.serialize(labels))
    assert res == data


def test_polyline_import_without_confidence():
    with open("tests/data/assets/ndjson/polyline_import.json", "r") as file:
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
                    confidence=0.58,
                    name="some-line",
                    feature_schema_id="cl6xnuwt95lqq07330tbb3mfd",
                    extra={
                        "uuid": "5ad9c52f-058d-49c8-a749-3f20b84f8cd4",
                    },
                    value=Line(
                        points=[
                            Point(x=2534.353, y=249.471),
                            Point(x=2429.492, y=182.092),
                            Point(x=2294.322, y=221.962),
                        ],
                    ),
                )
            ],
        )
    ]

    res = list(NDJsonConverter.serialize(labels))
    assert res == data
