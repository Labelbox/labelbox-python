from copy import copy
import labelbox.types as lb_types
from labelbox.data.serialization import NDJsonConverter
from labelbox.data.serialization.ndjson.objects import NDDicomSegments, NDDicomSegment, NDDicomLine, NDSegments, NDSegment, NDFrameLine

dicom_polyline_annotations = [
    lb_types.DICOMObjectAnnotation(uuid="dicom-object-uid",
                                   name="dicom_polyline",
                                   frame=2,
                                   value=lb_types.Line(points=[
                                       lb_types.Point(x=680, y=100),
                                       lb_types.Point(x=100, y=190),
                                       lb_types.Point(x=190, y=220)
                                   ]),
                                   segment_index=0,
                                   keyframe=True,
                                   group_key=lb_types.GroupKey.AXIAL)
]

label = lb_types.Label(data=lb_types.DicomData(uid="test-uid"),
                       annotations=dicom_polyline_annotations)
label_with_global_key = lb_types.Label(
    data=lb_types.DicomData(global_key="test-global-key"),
    annotations=dicom_polyline_annotations)

label_ndjson = {
    'classifications': [],
    'dataRow': {
        'id': 'test-uid'
    },
    'name':
        'dicom_polyline',
    'groupKey':
        'axial',
    'segments': [{
        'keyframes': [{
            'frame':
                2,
            'line': [
                {
                    'x': 680.0,
                    'y': 100.0
                },
                {
                    'x': 100.0,
                    'y': 190.0
                },
                {
                    'x': 190.0,
                    'y': 220.0
                },
            ]
        }]
    }],
}

label_ndjson_with_global_key = {
    'classifications': [],
    'dataRow': {
        'globalKey': 'test-global-key'
    },
    'name':
        'dicom_polyline',
    'groupKey':
        'axial',
    'segments': [{
        'keyframes': [{
            'frame':
                2,
            'line': [
                {
                    'x': 680.0,
                    'y': 100.0
                },
                {
                    'x': 100.0,
                    'y': 190.0
                },
                {
                    'x': 190.0,
                    'y': 220.0
                },
            ]
        }]
    }],
}


def test_serialize_dicom_polyline_annotation():
    serialized_label = next(NDJsonConverter().serialize([label]))
    serialized_label.pop('uuid')
    assert serialized_label == label_ndjson


def test_serialize_dicom_polyline_annotation_with_global_key():
    serialized_label = next(NDJsonConverter().serialize([label_with_global_key
                                                        ]))
    serialized_label.pop('uuid')
    assert serialized_label == label_ndjson_with_global_key


def test_deserialize_dicom_polyline_annotation():
    deserialized_label = next(NDJsonConverter().deserialize([label_ndjson]))
    deserialized_label.annotations[0].extra.pop('uuid')
    assert deserialized_label == label


def test_deserialize_dicom_polyline_annotation_with_global_key():
    deserialized_label = next(NDJsonConverter().deserialize(
        [label_ndjson_with_global_key]))
    deserialized_label.annotations[0].extra.pop('uuid')
    assert deserialized_label == label_with_global_key


def test_serialize_deserialize_dicom_polyline_annotation():
    labels = list(NDJsonConverter.deserialize([label_ndjson]))
    res = list(NDJsonConverter.serialize(labels))
    res[0].pop('uuid')
    assert res == [label_ndjson]


def test_serialize_deserialize_dicom_polyline_annotation_with_global_key():
    labels = list(NDJsonConverter.deserialize([label_ndjson_with_global_key]))
    res = list(NDJsonConverter.serialize(labels))
    res[0].pop('uuid')
    assert res == [label_ndjson_with_global_key]


def test_deserialize_nd_dicom_segments():
    nd_dicom_segments = NDDicomSegments(**label_ndjson)
    assert isinstance(nd_dicom_segments, NDDicomSegments)
    assert isinstance(nd_dicom_segments.segments[0], NDDicomSegment)
    assert isinstance(nd_dicom_segments.segments[0].keyframes[0], NDDicomLine)
