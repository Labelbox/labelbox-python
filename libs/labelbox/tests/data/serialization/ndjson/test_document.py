import json
from labelbox.data.annotation_types.data.generic_data_row_data import (
    GenericDataRowData,
)
from labelbox.data.mixins import CustomMetric
import labelbox.types as lb_types
from labelbox.data.serialization.ndjson.converter import NDJsonConverter
from labelbox.types import (
    Label,
    ObjectAnnotation,
    RectangleUnit,
    Point,
    DocumentRectangle,
    DocumentEntity,
    DocumentTextSelection,
)

bbox_annotation = lb_types.ObjectAnnotation(
    name="bounding_box",  # must match your ontology feature's name
    value=lb_types.DocumentRectangle(
        start=lb_types.Point(x=42.799, y=86.498),  # Top left
        end=lb_types.Point(x=141.911, y=303.195),  # Bottom right
        page=1,
        unit=lb_types.RectangleUnit.POINTS,
    ),
)
bbox_labels = [
    lb_types.Label(
        data=lb_types.GenericDataRowData(global_key="test-global-key"),
        annotations=[bbox_annotation],
    )
]
bbox_ndjson = [
    {
        "bbox": {
            "height": 216.697,
            "left": 42.799,
            "top": 86.498,
            "width": 99.112,
        },
        "classifications": [],
        "dataRow": {"globalKey": "test-global-key"},
        "name": "bounding_box",
        "page": 1,
        "unit": "POINTS",
    }
]


def round_dict(data):
    if isinstance(data, dict):
        for key in data:
            if isinstance(data[key], (int, float)):
                data[key] = int(data[key])
            elif isinstance(data[key], dict):
                data[key] = round_dict(data[key])
            elif isinstance(data[key], (list, tuple)):
                data[key] = [round_dict(r) for r in data[key]]

    return data


def test_pdf():
    """
    Tests a pdf file with bbox annotations only
    """
    with open("tests/data/assets/ndjson/pdf_import.json", "r") as f:
        data = json.load(f)
    labels = [
        Label(
            uid=None,
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
                    name="boxy",
                    feature_schema_id="cl6xnuwt95lqq07330tbb3mfd",
                    extra={
                        "uuid": "5ad9c52f-058d-49c8-a749-3f20b84f8cd4",
                    },
                    value=DocumentRectangle(
                        start=Point(x=32.45, y=162.73),
                        end=Point(x=134.11, y=550.9),
                        page=4,
                        unit=RectangleUnit.POINTS,
                    ),
                ),
                ObjectAnnotation(
                    name="boxy",
                    feature_schema_id="cl6xnuwt95lqq07330tbb3mfd",
                    extra={
                        "uuid": "20eeef88-0294-49b4-a815-86588476bc6f",
                    },
                    value=DocumentRectangle(
                        start=Point(x=251.42, y=223.26),
                        end=Point(x=438.2, y=680.3),
                        page=7,
                        unit=RectangleUnit.POINTS,
                    ),
                ),
                ObjectAnnotation(
                    custom_metrics=[
                        CustomMetric(name="customMetric1", value=0.5),
                        CustomMetric(name="customMetric2", value=0.3),
                    ],
                    confidence=0.99,
                    name="boxy",
                    feature_schema_id="cl6xnuwt95lqq07330tbb3mfd",
                    extra={
                        "uuid": "641a8944-3938-409c-b4eb-dea354ed06e5",
                    },
                    value=DocumentRectangle(
                        start=Point(x=218.17, y=32.52),
                        end=Point(x=328.73, y=264.25),
                        page=6,
                        unit=RectangleUnit.POINTS,
                    ),
                ),
                ObjectAnnotation(
                    custom_metrics=[
                        CustomMetric(name="customMetric1", value=0.5),
                        CustomMetric(name="customMetric2", value=0.3),
                    ],
                    confidence=0.89,
                    name="boxy",
                    feature_schema_id="cl6xnuwt95lqq07330tbb3mfd",
                    extra={
                        "uuid": "ebe4da7d-08b3-480a-8d15-26552b7f011c",
                    },
                    value=DocumentRectangle(
                        start=Point(x=4.25, y=117.39),
                        end=Point(x=169.08, y=574.3100000000001),
                        page=7,
                        unit=RectangleUnit.POINTS,
                    ),
                ),
                ObjectAnnotation(
                    name="boxy",
                    feature_schema_id="cl6xnuwt95lqq07330tbb3mfd",
                    extra={
                        "uuid": "35c41855-575f-42cc-a2f9-1f06237e9b63",
                    },
                    value=DocumentRectangle(
                        start=Point(x=217.28, y=82.13),
                        end=Point(x=299.71000000000004, y=361.89),
                        page=8,
                        unit=RectangleUnit.POINTS,
                    ),
                ),
                ObjectAnnotation(
                    name="boxy",
                    feature_schema_id="cl6xnuwt95lqq07330tbb3mfd",
                    extra={
                        "uuid": "1b009654-bc17-42a2-8a71-160e7808c403",
                    },
                    value=DocumentRectangle(
                        start=Point(x=83.34, y=298.12),
                        end=Point(x=83.72, y=501.95000000000005),
                        page=3,
                        unit=RectangleUnit.POINTS,
                    ),
                ),
            ],
        ),
        Label(
            data=GenericDataRowData(
                uid="ckrb1sf1i1g7i0ybcdc6oc8ct",
            ),
            annotations=[
                ObjectAnnotation(
                    name="named_entity",
                    feature_schema_id="cl6xnuwt95lqq07330tbb3mfd",
                    extra={
                        "uuid": "f6879f59-d2b5-49c2-aceb-d9e8dc478673",
                    },
                    value=DocumentEntity(
                        text_selections=[
                            DocumentTextSelection(
                                token_ids=[
                                    "3f984bf3-1d61-44f5-b59a-9658a2e3440f",
                                    "3bf00b56-ff12-4e52-8cc1-08dbddb3c3b8",
                                    "6e1c3420-d4b7-4c5a-8fd6-ead43bf73d80",
                                    "87a43d32-af76-4a1d-b262-5c5f4d5ace3a",
                                    "e8606e8a-dfd9-4c49-a635-ad5c879c75d0",
                                    "67c7c19e-4654-425d-bf17-2adb8cf02c30",
                                    "149c5e80-3e07-49a7-ab2d-29ddfe6a38fa",
                                    "b0e94071-2187-461e-8e76-96c58738a52c",
                                ],
                                group_id="2f4336f4-a07e-4e0a-a9e1-5629b03b719b",
                                page=1,
                            )
                        ]
                    ),
                )
            ],
        ),
    ]

    res = list(NDJsonConverter.serialize(labels))
    assert [round_dict(x) for x in res] == [round_dict(x) for x in data]


def test_pdf_with_name_only():
    """
    Tests a pdf file with bbox annotations only
    """
    with open("tests/data/assets/ndjson/pdf_import_name_only.json", "r") as f:
        data = json.load(f)

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
                    confidence=0.99,
                    name="boxy",
                    feature_schema_id=None,
                    extra={
                        "uuid": "5ad9c52f-058d-49c8-a749-3f20b84f8cd4",
                    },
                    value=DocumentRectangle(
                        start=Point(x=32.45, y=162.73),
                        end=Point(x=134.11, y=550.9),
                        page=4,
                        unit=RectangleUnit.POINTS,
                    ),
                ),
                ObjectAnnotation(
                    name="boxy",
                    extra={
                        "uuid": "20eeef88-0294-49b4-a815-86588476bc6f",
                    },
                    value=DocumentRectangle(
                        start=Point(x=251.42, y=223.26),
                        end=Point(x=438.2, y=680.3),
                        page=7,
                        unit=RectangleUnit.POINTS,
                    ),
                ),
                ObjectAnnotation(
                    name="boxy",
                    extra={
                        "uuid": "641a8944-3938-409c-b4eb-dea354ed06e5",
                    },
                    value=DocumentRectangle(
                        start=Point(x=218.17, y=32.52),
                        end=Point(x=328.73, y=264.25),
                        page=6,
                        unit=RectangleUnit.POINTS,
                    ),
                ),
                ObjectAnnotation(
                    custom_metrics=[
                        CustomMetric(name="customMetric1", value=0.5),
                        CustomMetric(name="customMetric2", value=0.3),
                    ],
                    confidence=0.74,
                    name="boxy",
                    extra={
                        "uuid": "ebe4da7d-08b3-480a-8d15-26552b7f011c",
                    },
                    value=DocumentRectangle(
                        start=Point(x=4.25, y=117.39),
                        end=Point(x=169.08, y=574.3100000000001),
                        page=7,
                        unit=RectangleUnit.POINTS,
                    ),
                ),
                ObjectAnnotation(
                    name="boxy",
                    extra={
                        "uuid": "35c41855-575f-42cc-a2f9-1f06237e9b63",
                    },
                    value=DocumentRectangle(
                        start=Point(x=217.28, y=82.13),
                        end=Point(x=299.71000000000004, y=361.89),
                        page=8,
                        unit=RectangleUnit.POINTS,
                    ),
                ),
                ObjectAnnotation(
                    name="boxy",
                    extra={
                        "uuid": "1b009654-bc17-42a2-8a71-160e7808c403",
                    },
                    value=DocumentRectangle(
                        start=Point(x=83.34, y=298.12),
                        end=Point(x=83.72, y=501.95000000000005),
                        page=3,
                        unit=RectangleUnit.POINTS,
                    ),
                ),
            ],
        ),
        Label(
            data=GenericDataRowData(
                uid="ckrb1sf1i1g7i0ybcdc6oc8ct",
            ),
            annotations=[
                ObjectAnnotation(
                    name="named_entity",
                    extra={
                        "uuid": "f6879f59-d2b5-49c2-aceb-d9e8dc478673",
                    },
                    value=DocumentEntity(
                        text_selections=[
                            DocumentTextSelection(
                                token_ids=[
                                    "3f984bf3-1d61-44f5-b59a-9658a2e3440f",
                                    "3bf00b56-ff12-4e52-8cc1-08dbddb3c3b8",
                                    "6e1c3420-d4b7-4c5a-8fd6-ead43bf73d80",
                                    "87a43d32-af76-4a1d-b262-5c5f4d5ace3a",
                                    "e8606e8a-dfd9-4c49-a635-ad5c879c75d0",
                                    "67c7c19e-4654-425d-bf17-2adb8cf02c30",
                                    "149c5e80-3e07-49a7-ab2d-29ddfe6a38fa",
                                    "b0e94071-2187-461e-8e76-96c58738a52c",
                                ],
                                group_id="2f4336f4-a07e-4e0a-a9e1-5629b03b719b",
                                page=1,
                            )
                        ]
                    ),
                )
            ],
        ),
    ]
    res = list(NDJsonConverter.serialize(labels))
    assert [round_dict(x) for x in res] == [round_dict(x) for x in data]


def test_pdf_bbox_serialize():
    serialized = list(NDJsonConverter.serialize(bbox_labels))
    serialized[0].pop("uuid")
    assert serialized == bbox_ndjson
