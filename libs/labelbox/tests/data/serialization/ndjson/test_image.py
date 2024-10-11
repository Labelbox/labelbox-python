import json
from labelbox.data.annotation_types.data.generic_data_row_data import (
    GenericDataRowData,
)
from labelbox.data.mixins import CustomMetric
import numpy as np
import cv2

from labelbox.data.serialization.ndjson.converter import NDJsonConverter
from labelbox.data.annotation_types import (
    Mask,
    Label,
    ObjectAnnotation,
    MaskData,
)
from labelbox.types import Rectangle, Polygon, Point


def round_dict(data):
    if isinstance(data, dict):
        for key in data:
            if isinstance(data[key], float):
                data[key] = int(data[key])
            elif isinstance(data[key], dict):
                data[key] = round_dict(data[key])
            elif isinstance(data[key], (list, tuple)):
                data[key] = [round_dict(r) for r in data[key]]

    return data


def test_image():
    with open("tests/data/assets/ndjson/image_import.json", "r") as file:
        data = json.load(file)

    labels = [
        Label(
            data=GenericDataRowData(
                uid="ckrazctum0z8a0ybc0b0o0g0v",
            ),
            annotations=[
                ObjectAnnotation(
                    custom_metrics=[
                        CustomMetric(name="customMetric1", value=0.4)
                    ],
                    confidence=0.851,
                    feature_schema_id="ckrazcueb16og0z6609jj7y3y",
                    extra={
                        "uuid": "b862c586-8614-483c-b5e6-82810f70cac0",
                    },
                    value=Rectangle(
                        start=Point(extra={}, x=2275.0, y=1352.0),
                        end=Point(extra={}, x=2414.0, y=1702.0),
                    ),
                ),
                ObjectAnnotation(
                    custom_metrics=[
                        CustomMetric(name="customMetric1", value=0.3)
                    ],
                    confidence=0.834,
                    feature_schema_id="ckrazcuec16ok0z66f956apb7",
                    extra={
                        "uuid": "751fc725-f7b6-48ed-89b0-dd7d94d08af6",
                    },
                    value=Mask(
                        mask=MaskData(
                            url="https://storage.labelbox.com/ckqcx1czn06830y61gh9v02cs%2F3e729327-f038-f66c-186e-45e921ef9717-1?Expires=1626806874672&KeyName=labelbox-assets-key-3&Signature=YsUOGKrsqmAZ68vT9BlPJOaRyLY",
                        ),
                        color=[255, 0, 0],
                    ),
                ),
                ObjectAnnotation(
                    custom_metrics=[
                        CustomMetric(name="customMetric1", value=0.9)
                    ],
                    confidence=0.986,
                    feature_schema_id="ckrazcuec16oi0z66dzrd8pfl",
                    extra={
                        "uuid": "43d719ac-5d7f-4aea-be00-2ebfca0900fd",
                    },
                    value=Polygon(
                        points=[
                            Point(x=10.0, y=20.0),
                            Point(x=15.0, y=20.0),
                            Point(x=20.0, y=25.0),
                            Point(x=10.0, y=20.0),
                        ],
                    ),
                ),
                ObjectAnnotation(
                    feature_schema_id="ckrazcuec16om0z66bhhh4tp7",
                    extra={
                        "uuid": "b98f3a45-3328-41a0-9077-373a8177ebf2",
                    },
                    value=Point(x=2122.0, y=1457.0),
                ),
            ],
        )
    ]

    res = list(NDJsonConverter.serialize(labels))
    del res[1]["mask"]["colorRGB"]  # JSON does not support tuples
    assert res == data


def test_image_with_name_only():
    with open(
        "tests/data/assets/ndjson/image_import_name_only.json", "r"
    ) as file:
        data = json.load(file)

    labels = [
        Label(
            data=GenericDataRowData(
                uid="ckrazctum0z8a0ybc0b0o0g0v",
            ),
            annotations=[
                ObjectAnnotation(
                    custom_metrics=[
                        CustomMetric(name="customMetric1", value=0.4)
                    ],
                    confidence=0.851,
                    name="ckrazcueb16og0z6609jj7y3y",
                    extra={
                        "uuid": "b862c586-8614-483c-b5e6-82810f70cac0",
                    },
                    value=Rectangle(
                        start=Point(extra={}, x=2275.0, y=1352.0),
                        end=Point(extra={}, x=2414.0, y=1702.0),
                    ),
                ),
                ObjectAnnotation(
                    custom_metrics=[
                        CustomMetric(name="customMetric1", value=0.3)
                    ],
                    confidence=0.834,
                    name="ckrazcuec16ok0z66f956apb7",
                    extra={
                        "uuid": "751fc725-f7b6-48ed-89b0-dd7d94d08af6",
                    },
                    value=Mask(
                        mask=MaskData(
                            url="https://storage.labelbox.com/ckqcx1czn06830y61gh9v02cs%2F3e729327-f038-f66c-186e-45e921ef9717-1?Expires=1626806874672&KeyName=labelbox-assets-key-3&Signature=YsUOGKrsqmAZ68vT9BlPJOaRyLY",
                        ),
                        color=[255, 0, 0],
                    ),
                ),
                ObjectAnnotation(
                    custom_metrics=[
                        CustomMetric(name="customMetric1", value=0.9)
                    ],
                    confidence=0.986,
                    name="ckrazcuec16oi0z66dzrd8pfl",
                    extra={
                        "uuid": "43d719ac-5d7f-4aea-be00-2ebfca0900fd",
                    },
                    value=Polygon(
                        points=[
                            Point(x=10.0, y=20.0),
                            Point(x=15.0, y=20.0),
                            Point(x=20.0, y=25.0),
                            Point(x=10.0, y=20.0),
                        ],
                    ),
                ),
                ObjectAnnotation(
                    name="ckrazcuec16om0z66bhhh4tp7",
                    extra={
                        "uuid": "b98f3a45-3328-41a0-9077-373a8177ebf2",
                    },
                    value=Point(x=2122.0, y=1457.0),
                ),
            ],
        )
    ]

    res = list(NDJsonConverter.serialize(labels))
    del res[1]["mask"]["colorRGB"]  # JSON does not support tuples
    assert res == data


def test_mask():
    data = [
        {
            "uuid": "b862c586-8614-483c-b5e6-82810f70cac0",
            "schemaId": "ckrazcueb16og0z6609jj7y3y",
            "dataRow": {"id": "ckrazctum0z8a0ybc0b0o0g0v"},
            "mask": {
                "png": "iVBORw0KGgoAAAANSUhEUgAAAAIAAAACCAAAAABX3VL4AAAADklEQVR4nGNgYGBkZAAAAAsAA+RRQXwAAAAASUVORK5CYII="
            },
            "confidence": 0.8,
            "customMetrics": [{"name": "customMetric1", "value": 0.4}],
            "classifications": [],
        },
        {
            "uuid": "751fc725-f7b6-48ed-89b0-dd7d94d08af6",
            "schemaId": "ckrazcuec16ok0z66f956apb7",
            "dataRow": {"id": "ckrazctum0z8a0ybc0b0o0g0v"},
            "mask": {
                "instanceURI": "https://storage.labelbox.com/ckqcx1czn06830y61gh9v02cs%2F3e729327-f038-f66c-186e-45e921ef9717-1?Expires=1626806874672&KeyName=labelbox-assets-key-3&Signature=YsUOGKrsqmAZ68vT9BlPJOaRyLY",
                "colorRGB": (255, 0, 0),
            },
            "classifications": [],
        },
    ]

    mask_numpy = np.array([[[1, 1, 0], [1, 0, 1]], [[1, 1, 1], [1, 1, 1]]])
    mask_numpy = mask_numpy.astype(np.uint8)

    labels = [
        Label(
            data=GenericDataRowData(
                uid="ckrazctum0z8a0ybc0b0o0g0v",
            ),
            annotations=[
                ObjectAnnotation(
                    custom_metrics=[
                        CustomMetric(name="customMetric1", value=0.4)
                    ],
                    confidence=0.8,
                    feature_schema_id="ckrazcueb16og0z6609jj7y3y",
                    extra={
                        "uuid": "b862c586-8614-483c-b5e6-82810f70cac0",
                    },
                    value=Mask(
                        mask=MaskData(arr=mask_numpy),
                        color=(1, 1, 1),
                    ),
                ),
                ObjectAnnotation(
                    feature_schema_id="ckrazcuec16ok0z66f956apb7",
                    extra={
                        "uuid": "751fc725-f7b6-48ed-89b0-dd7d94d08af6",
                    },
                    value=Mask(
                        extra={},
                        mask=MaskData(
                            url="https://storage.labelbox.com/ckqcx1czn06830y61gh9v02cs%2F3e729327-f038-f66c-186e-45e921ef9717-1?Expires=1626806874672&KeyName=labelbox-assets-key-3&Signature=YsUOGKrsqmAZ68vT9BlPJOaRyLY",
                        ),
                        color=(255, 0, 0),
                    ),
                ),
            ],
        )
    ]
    res = list(NDJsonConverter.serialize(labels))

    assert res == data


def test_mask_from_arr():
    mask_arr = np.round(np.zeros((32, 32))).astype(np.uint8)
    mask_arr = cv2.rectangle(mask_arr, (5, 5), (10, 10), (1, 1), -1)

    label = Label(
        annotations=[
            ObjectAnnotation(
                feature_schema_id="1" * 25,
                value=Mask(
                    mask=MaskData.from_2D_arr(arr=mask_arr), color=(1, 1, 1)
                ),
            )
        ],
        data=GenericDataRowData(uid="0" * 25),
    )
    res = next(NDJsonConverter.serialize([label]))
    res.pop("uuid")
    assert res == {
        "classifications": [],
        "schemaId": "1" * 25,
        "dataRow": {"id": "0" * 25},
        "mask": {
            "png": "iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAAAAABWESUoAAAAHklEQVR4nGNgGAKAEYn8j00BEyETBoOCUTAKhhwAAJW+AQwvpePVAAAAAElFTkSuQmCC"
        },
    }
