import json
import numpy as np
import cv2

from labelbox.data.serialization.ndjson.converter import NDJsonConverter
from labelbox.data.annotation_types import (
    Mask,
    Label,
    ObjectAnnotation,
    ImageData,
    MaskData,
)


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

    res = list(NDJsonConverter.deserialize(data))
    res = list(NDJsonConverter.serialize(res))

    for r in res:
        r.pop("classifications", None)
    assert [round_dict(x) for x in res] == [round_dict(x) for x in data]


def test_image_with_name_only():
    with open(
        "tests/data/assets/ndjson/image_import_name_only.json", "r"
    ) as file:
        data = json.load(file)

    res = list(NDJsonConverter.deserialize(data))
    res = list(NDJsonConverter.serialize(res))
    for r in res:
        r.pop("classifications", None)
    assert [round_dict(x) for x in res] == [round_dict(x) for x in data]


def test_mask():
    data = [
        {
            "uuid": "b862c586-8614-483c-b5e6-82810f70cac0",
            "schemaId": "ckrazcueb16og0z6609jj7y3y",
            "dataRow": {"id": "ckrazctum0z8a0ybc0b0o0g0v"},
            "mask": {
                "png": "iVBORw0KGgoAAAANSUhEUgAAAAoAAAAKCAAAAACoWZBhAAAAMklEQVR4nD3MuQ3AQADDMOqQ/Vd2ijytaSiZLAcYuyLEYYYl9cvrlGftTHvsYl+u/3EDv0QLI8Z7FlwAAAAASUVORK5CYII="
            },
            "confidence": 0.8,
            "customMetrics": [{"name": "customMetric1", "value": 0.4}],
        },
        {
            "uuid": "751fc725-f7b6-48ed-89b0-dd7d94d08af6",
            "schemaId": "ckrazcuec16ok0z66f956apb7",
            "dataRow": {"id": "ckrazctum0z8a0ybc0b0o0g0v"},
            "mask": {
                "instanceURI": "https://storage.labelbox.com/ckqcx1czn06830y61gh9v02cs%2F3e729327-f038-f66c-186e-45e921ef9717-1?Expires=1626806874672&KeyName=labelbox-assets-key-3&Signature=YsUOGKrsqmAZ68vT9BlPJOaRyLY",
                "colorRGB": [255, 0, 0],
            },
        },
    ]
    res = list(NDJsonConverter.deserialize(data))
    res = list(NDJsonConverter.serialize(res))
    for r in res:
        r.pop("classifications", None)

    assert [round_dict(x) for x in res] == [round_dict(x) for x in data]


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
        data=ImageData(uid="0" * 25),
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
