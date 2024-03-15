import json

from labelbox.data.serialization.labelbox_v1.converter import LBV1Converter


def round_dict(data):
    for key in data:
        if isinstance(data[key], float):
            data[key] = int(data[key])
        elif isinstance(data[key], dict):
            data[key] = round_dict(data[key])
    return data


def test_video():
    payload = json.load(
        open('tests/data/assets/labelbox_v1/video_export.json', 'r'))
    collection = LBV1Converter.deserialize([payload])
    serialized = next(LBV1Converter.serialize(collection))
    payload['media_type'] = 'video'
    payload['Global Key'] = None
    assert serialized.keys() == payload.keys()
    for key in serialized:
        if key != 'Label':
            assert serialized[key] == payload[key]
        elif key == 'Label':
            for annotation_a, annotation_b in zip(serialized[key],
                                                  payload[key]):
                assert annotation_a['frameNumber'] == annotation_b[
                    'frameNumber']
                assert annotation_a['classifications'] == annotation_b[
                    'classifications']

                for obj_a, obj_b in zip(annotation_a['objects'],
                                        annotation_b['objects']):
                    obj_b['page'] = None
                    obj_b['unit'] = None
                    obj_a = round_dict(obj_a)
                    obj_b = round_dict(obj_b)
                    assert obj_a == obj_b
