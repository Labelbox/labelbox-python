import json

from labelbox.data.serialization.labelbox_v1.converter import LBV1Converter


def test_image():
    with open('tests/data/assets/labelbox_v1/image_export.json', 'r') as file:
        payload = json.load(file)

    collection = LBV1Converter.deserialize([payload])
    serialized = next(LBV1Converter.serialize(collection))

    assert serialized.keys() == payload.keys()
    for key in serialized:
        if key != 'Label':
            assert serialized[key] == payload[key]
        elif key == 'Label':
            for annotation_a, annotation_b in zip(serialized[key]['objects'],
                                                  payload[key]['objects']):
                if not len(annotation_a['classifications']):
                    # We don't add a classification key to the payload if there is no classifications.
                    annotation_a.pop('classifications')
                assert annotation_a == annotation_b
