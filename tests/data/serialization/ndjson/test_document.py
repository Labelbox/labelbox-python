import json
import labelbox.types as lb_types
from labelbox.data.serialization.ndjson.converter import NDJsonConverter

bbox_annotation = lb_types.ObjectAnnotation(
    name="bounding_box",  # must match your ontology feature's name
    value=lb_types.DocumentRectangle(
        start=lb_types.Point(x=42.799, y=86.498),  # Top left
        end=lb_types.Point(x=141.911, y=303.195),  # Bottom right
        page=1,
        unit=lb_types.RectangleUnit.POINTS))
bbox_labels = [
    lb_types.Label(data=lb_types.DocumentData(global_key='test-global-key'),
                   annotations=[bbox_annotation])
]
bbox_ndjson = [{
    'bbox': {
        'height': 216.697,
        'left': 42.799,
        'top': 86.498,
        'width': 99.112,
    },
    'classifications': [],
    'dataRow': {
        'globalKey': 'test-global-key'
    },
    'name': 'bounding_box',
    'page': 1,
    'unit': 'POINTS'
}]


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
    with open('tests/data/assets/ndjson/pdf_import.json', 'r') as f:
        data = json.load(f)
    res = list(NDJsonConverter.deserialize(data))
    res = list(NDJsonConverter.serialize(res))
    assert [round_dict(x) for x in res] == [round_dict(x) for x in data]
    f.close()


def test_pdf_with_name_only():
    """
    Tests a pdf file with bbox annotations only
    """
    with open('tests/data/assets/ndjson/pdf_import_name_only.json', 'r') as f:
        data = json.load(f)
    res = list(NDJsonConverter.deserialize(data))
    res = list(NDJsonConverter.serialize(res))
    assert [round_dict(x) for x in res] == [round_dict(x) for x in data]
    f.close()


def test_pdf_bbox_serialize():
    serialized = list(NDJsonConverter.serialize(bbox_labels))
    serialized[0].pop('uuid')
    assert serialized == bbox_ndjson


def test_pdf_bbox_deserialize():
    deserialized = list(NDJsonConverter.deserialize(bbox_ndjson))
    deserialized[0].annotations[0].extra = {}
    assert deserialized[0].annotations == bbox_labels[0].annotations
