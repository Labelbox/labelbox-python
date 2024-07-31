import json
import labelbox.types as lb_types
from labelbox.data.serialization.ndjson.converter import NDJsonConverter

DATAROW_ID = "ckrb1sf1i1g7i0ybcdc6oc8ct"


def test_rectangle():
    with open('tests/data/assets/ndjson/rectangle_import.json', 'r') as file:
        data = json.load(file)
    res = list(NDJsonConverter.deserialize(data))
    res = list(NDJsonConverter.serialize(res))
    assert res == data


def test_rectangle_inverted_start_end_points():
    with open('tests/data/assets/ndjson/rectangle_import.json', 'r') as file:
        data = json.load(file)

    bbox = lb_types.ObjectAnnotation(
        name="bbox",
        value=lb_types.Rectangle(
            start=lb_types.Point(x=81, y=69),
            end=lb_types.Point(x=38, y=28),
        ),
        extra={"uuid": "c1be3a57-597e-48cb-8d8d-a852665f9e72"})

    label = lb_types.Label(data={"uid":DATAROW_ID},
                           annotations=[bbox])

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
            "page": None,
            "unit": None
        })

    label = lb_types.Label(data={"uid":DATAROW_ID},
                           annotations=[expected_bbox])

    res = list(NDJsonConverter.deserialize(res))
    assert res == [label]


def test_rectangle_mixed_start_end_points():
    with open('tests/data/assets/ndjson/rectangle_import.json', 'r') as file:
        data = json.load(file)

    bbox = lb_types.ObjectAnnotation(
        name="bbox",
        value=lb_types.Rectangle(
            start=lb_types.Point(x=81, y=28),
            end=lb_types.Point(x=38, y=69),
        ),
        extra={"uuid": "c1be3a57-597e-48cb-8d8d-a852665f9e72"})

    label = lb_types.Label(data={"uid":DATAROW_ID},
                           annotations=[bbox])

    res = list(NDJsonConverter.serialize([label]))
    assert res == data

    bbox = lb_types.ObjectAnnotation(
        name="bbox",
        value=lb_types.Rectangle(
            start=lb_types.Point(x=38, y=28),
            end=lb_types.Point(x=81, y=69),
        ),
        extra={
            "uuid": "c1be3a57-597e-48cb-8d8d-a852665f9e72",
            "page": None,
            "unit": None
        })

    label = lb_types.Label(data={"uid":DATAROW_ID},
                           annotations=[bbox])

    res = list(NDJsonConverter.deserialize(res))
    assert res == [label]


def test_benchmark_reference_label_flag_enabled():
    bbox = lb_types.ObjectAnnotation(
        name="bbox",
        value=lb_types.Rectangle(
            start=lb_types.Point(x=81, y=28),
            end=lb_types.Point(x=38, y=69),
        ),
        extra={"uuid": "c1be3a57-597e-48cb-8d8d-a852665f9e72"}
    )

    label = lb_types.Label(
        data={"uid":DATAROW_ID},
        annotations=[bbox],
        is_benchmark_reference=True
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
        extra={"uuid": "c1be3a57-597e-48cb-8d8d-a852665f9e72"}
    )

    label = lb_types.Label(
        data={"uid":DATAROW_ID},
        annotations=[bbox],
        is_benchmark_reference=False
    )

    res = list(NDJsonConverter.serialize([label]))
    assert not res[0].get("isBenchmarkReferenceLabel")
