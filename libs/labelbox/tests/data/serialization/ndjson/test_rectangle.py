import json
from labelbox.data.annotation_types.data.generic_data_row_data import (
    GenericDataRowData,
)
import labelbox.types as lb_types
from labelbox.data.serialization.ndjson.converter import NDJsonConverter
from labelbox.types import Label, ObjectAnnotation, Rectangle, Point

DATAROW_ID = "ckrb1sf1i1g7i0ybcdc6oc8ct"


def test_rectangle():
    with open("tests/data/assets/ndjson/rectangle_import.json", "r") as file:
        data = json.load(file)
    labels = [
        Label(
            data=GenericDataRowData(
                uid="ckrb1sf1i1g7i0ybcdc6oc8ct",
            ),
            annotations=[
                ObjectAnnotation(
                    name="bbox",
                    extra={
                        "uuid": "c1be3a57-597e-48cb-8d8d-a852665f9e72",
                    },
                    value=Rectangle(
                        start=Point(x=38.0, y=28.0),
                        end=Point(x=81.0, y=69.0),
                    ),
                )
            ],
        )
    ]
    res = list(NDJsonConverter.serialize(labels))
    assert res == data


def test_rectangle_inverted_start_end_points():
    with open("tests/data/assets/ndjson/rectangle_import.json", "r") as file:
        data = json.load(file)

    bbox = lb_types.ObjectAnnotation(
        name="bbox",
        value=lb_types.Rectangle(
            start=lb_types.Point(x=81, y=69),
            end=lb_types.Point(x=38, y=28),
        ),
        extra={"uuid": "c1be3a57-597e-48cb-8d8d-a852665f9e72"},
    )

    label = lb_types.Label(data={"uid": DATAROW_ID}, annotations=[bbox])

    res = list(NDJsonConverter.serialize([label]))
    assert res == data

    expected_bbox = lb_types.ObjectAnnotation(
        name="bbox",
        value=lb_types.Rectangle(
            start=lb_types.Point(x=38, y=28),
            end=lb_types.Point(x=81, y=69),
        ),
        extra={
            "uuid": "c1be3a57-597e-48cb-8d8d-a852665f9e72",
        },
    )

    label = lb_types.Label(
        data={"uid": DATAROW_ID}, annotations=[expected_bbox]
    )

    data = list(NDJsonConverter.serialize([label]))

    assert res == data


def test_rectangle_mixed_start_end_points():
    with open("tests/data/assets/ndjson/rectangle_import.json", "r") as file:
        data = json.load(file)

    bbox = lb_types.ObjectAnnotation(
        name="bbox",
        value=lb_types.Rectangle(
            start=lb_types.Point(x=81, y=28),
            end=lb_types.Point(x=38, y=69),
        ),
        extra={"uuid": "c1be3a57-597e-48cb-8d8d-a852665f9e72"},
    )

    label = lb_types.Label(data={"uid": DATAROW_ID}, annotations=[bbox])

    res = list(NDJsonConverter.serialize([label]))
    assert res == data

    bbox = lb_types.ObjectAnnotation(
        name="bbox",
        value=lb_types.Rectangle(
            start=lb_types.Point(x=38, y=28),
            end=lb_types.Point(x=81, y=69),
        ),
        extra={"uuid": "c1be3a57-597e-48cb-8d8d-a852665f9e72"},
    )

    label = lb_types.Label(data={"uid": DATAROW_ID}, annotations=[bbox])

    data = list(NDJsonConverter.serialize([label]))
    assert res == data


def test_benchmark_reference_label_flag_enabled():
    bbox = lb_types.ObjectAnnotation(
        name="bbox",
        value=lb_types.Rectangle(
            start=lb_types.Point(x=81, y=28),
            end=lb_types.Point(x=38, y=69),
        ),
        extra={"uuid": "c1be3a57-597e-48cb-8d8d-a852665f9e72"},
    )

    label = lb_types.Label(
        data={"uid": DATAROW_ID},
        annotations=[bbox],
        is_benchmark_reference=True,
    )

    res = list(NDJsonConverter.serialize([label]))
    assert res[0]["isBenchmarkReferenceLabel"]


def test_benchmark_reference_label_flag_disabled():
    bbox = lb_types.ObjectAnnotation(
        name="bbox",
        value=lb_types.Rectangle(
            start=lb_types.Point(x=81, y=28),
            end=lb_types.Point(x=38, y=69),
        ),
        extra={"uuid": "c1be3a57-597e-48cb-8d8d-a852665f9e72"},
    )

    label = lb_types.Label(
        data={"uid": DATAROW_ID},
        annotations=[bbox],
        is_benchmark_reference=False,
    )

    res = list(NDJsonConverter.serialize([label]))
    assert not res[0].get("isBenchmarkReferenceLabel")
