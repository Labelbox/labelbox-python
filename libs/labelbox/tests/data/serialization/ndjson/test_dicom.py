from copy import copy
import pytest
import base64
import labelbox.types as lb_types
from labelbox.data.serialization import NDJsonConverter
from labelbox.data.serialization.ndjson.objects import (
    NDDicomSegments,
    NDDicomSegment,
    NDDicomLine,
)

"""
Polyline test data
"""

dicom_polyline_annotations = [
    lb_types.DICOMObjectAnnotation(
        uuid="78a8a027-9089-420c-8348-6099eb77e4aa",
        name="dicom_polyline",
        frame=2,
        value=lb_types.Line(
            points=[
                lb_types.Point(x=680, y=100),
                lb_types.Point(x=100, y=190),
                lb_types.Point(x=190, y=220),
            ]
        ),
        segment_index=0,
        keyframe=True,
        group_key=lb_types.GroupKey.AXIAL,
    )
]

polyline_label = lb_types.Label(
    data=lb_types.DicomData(uid="test-uid"),
    annotations=dicom_polyline_annotations,
)

polyline_annotation_ndjson = {
    "classifications": [],
    "dataRow": {"id": "test-uid"},
    "name": "dicom_polyline",
    "groupKey": "axial",
    "segments": [
        {
            "keyframes": [
                {
                    "frame": 2,
                    "line": [
                        {"x": 680.0, "y": 100.0},
                        {"x": 100.0, "y": 190.0},
                        {"x": 190.0, "y": 220.0},
                    ],
                    "classifications": [],
                }
            ]
        }
    ],
}

polyline_with_global_key = lb_types.Label(
    data=lb_types.DicomData(global_key="test-global-key"),
    annotations=dicom_polyline_annotations,
)

polyline_annotation_ndjson_with_global_key = copy(polyline_annotation_ndjson)
polyline_annotation_ndjson_with_global_key["dataRow"] = {
    "globalKey": "test-global-key"
}
"""
Video test data
"""

instance_uri_1 = "https://storage.labelbox.com/cjhfn5y6s0pk507024nz1ocys%2F1d60856c-59b7-3060-2754-83f7e93e0d01-1?Expires=1666901963361&KeyName=labelbox-assets-key-3&Signature=t-2s2DB4YjFuWEFak0wxYqfBfZA"
instance_uri_5 = "https://storage.labelbox.com/cjhfn5y6s0pk507024nz1ocys1%2F1d60856c-59b7-3060-2754-83f7e93e0d01-1?Expires=1666901963361&KeyName=labelbox-assets-key-3&Signature=t-2s2DB4YjFuWEFak0wxYqfBfZA"
frames = [
    lb_types.MaskFrame(index=1, instance_uri=instance_uri_1),
    lb_types.MaskFrame(index=5, instance_uri=instance_uri_5),
]
instances = [
    lb_types.MaskInstance(color_rgb=(0, 0, 255), name="mask1"),
    lb_types.MaskInstance(color_rgb=(0, 255, 0), name="mask2"),
    lb_types.MaskInstance(color_rgb=(255, 0, 0), name="mask3"),
]

video_mask_annotation = lb_types.VideoMaskAnnotation(
    frames=frames, instances=instances
)

video_mask_annotation_ndjson = {
    "dataRow": {"id": "test-uid"},
    "masks": {
        "frames": [
            {"index": 1, "instanceURI": instance_uri_1},
            {"index": 5, "instanceURI": instance_uri_5},
        ],
        "instances": [
            {"colorRGB": (0, 0, 255), "name": "mask1"},
            {"colorRGB": (0, 255, 0), "name": "mask2"},
            {"colorRGB": (255, 0, 0), "name": "mask3"},
        ],
    },
}

video_mask_annotation_ndjson_with_global_key = copy(
    video_mask_annotation_ndjson
)
video_mask_annotation_ndjson_with_global_key["dataRow"] = {
    "globalKey": "test-global-key"
}

video_mask_label = lb_types.Label(
    data=lb_types.VideoData(uid="test-uid"), annotations=[video_mask_annotation]
)

video_mask_label_with_global_key = lb_types.Label(
    data=lb_types.VideoData(global_key="test-global-key"),
    annotations=[video_mask_annotation],
)
"""
DICOM Mask test data
"""

dicom_mask_annotation = lb_types.DICOMMaskAnnotation(
    name="dicom_mask",
    group_key=lb_types.GroupKey.AXIAL,
    frames=frames,
    instances=instances,
)

dicom_mask_label = lb_types.Label(
    data=lb_types.DicomData(uid="test-uid"), annotations=[dicom_mask_annotation]
)

dicom_mask_label_with_global_key = lb_types.Label(
    data=lb_types.DicomData(global_key="test-global-key"),
    annotations=[dicom_mask_annotation],
)

dicom_mask_annotation_ndjson = copy(video_mask_annotation_ndjson)
dicom_mask_annotation_ndjson["groupKey"] = "axial"
dicom_mask_annotation_ndjson_with_global_key = copy(
    dicom_mask_annotation_ndjson
)
dicom_mask_annotation_ndjson_with_global_key["dataRow"] = {
    "globalKey": "test-global-key"
}
"""
Tests
"""

labels = [
    polyline_label,
    polyline_with_global_key,
    dicom_mask_label,
    dicom_mask_label_with_global_key,
    video_mask_label,
    video_mask_label_with_global_key,
]
ndjsons = [
    polyline_annotation_ndjson,
    polyline_annotation_ndjson_with_global_key,
    dicom_mask_annotation_ndjson,
    dicom_mask_annotation_ndjson_with_global_key,
    video_mask_annotation_ndjson,
    video_mask_annotation_ndjson_with_global_key,
]
labels_ndjsons = list(zip(labels, ndjsons))


def test_deserialize_nd_dicom_segments():
    nd_dicom_segments = NDDicomSegments(**polyline_annotation_ndjson)
    assert isinstance(nd_dicom_segments, NDDicomSegments)
    assert isinstance(nd_dicom_segments.segments[0], NDDicomSegment)
    assert isinstance(nd_dicom_segments.segments[0].keyframes[0], NDDicomLine)


@pytest.mark.parametrize("label, ndjson", labels_ndjsons)
def test_serialize_label(label, ndjson):
    serialized_label = next(NDJsonConverter().serialize([label]))
    if "uuid" in serialized_label:
        serialized_label.pop("uuid")
    assert serialized_label == ndjson


@pytest.mark.parametrize("label, ndjson", labels_ndjsons)
def test_deserialize_label(label, ndjson):
    deserialized_label = next(NDJsonConverter().deserialize([ndjson]))
    if hasattr(deserialized_label.annotations[0], "extra"):
        deserialized_label.annotations[0].extra = {}
    for i, annotation in enumerate(deserialized_label.annotations):
        if hasattr(annotation, "frames"):
            assert annotation.frames == label.annotations[i].frames
        if hasattr(annotation, "value"):
            assert annotation.value == label.annotations[i].value


@pytest.mark.parametrize("label", labels)
def test_serialize_deserialize_label(label):
    serialized = list(NDJsonConverter.serialize([label]))
    deserialized = list(NDJsonConverter.deserialize(serialized))
    if hasattr(deserialized[0].annotations[0], "extra"):
        deserialized[0].annotations[0].extra = {}
    for i, annotation in enumerate(deserialized[0].annotations):
        if hasattr(annotation, "frames"):
            assert annotation.frames == label.annotations[i].frames
        if hasattr(annotation, "value"):
            assert annotation.value == label.annotations[i].value
