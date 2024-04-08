import json

import pytest

from labelbox.data.serialization.labelbox_v1.converter import LBV1Converter


def test_image():
    file_path = 'tests/data/assets/labelbox_v1/unkown_media_type_export.json'
    with open(file_path, 'r') as file:
        payload = json.load(file)

    collection = list(LBV1Converter.deserialize(payload))
    # One of the data rows is broken.
    assert len(collection) != len(payload)

    for row in payload:
        row['media_type'] = 'image'
        row['Global Key'] = None

    collection = LBV1Converter.deserialize(payload)
    for idx, serialized in enumerate(LBV1Converter.serialize(collection)):
        assert serialized.keys() == payload[idx].keys()
        for key in serialized:
            if key != 'Label':
                assert serialized[key] == payload[idx][key]
            elif key == 'Label':
                for annotation_a, annotation_b in zip(
                        serialized[key]['objects'],
                        payload[idx][key]['objects']):
                    if not len(annotation_a['classifications']):
                        # We don't add a classification key to the payload if there is no classifications.
                        annotation_a.pop('classifications')
                    annotation_b['page'] = None
                    annotation_b['unit'] = None

                    if isinstance(annotation_b.get('classifications'),
                                  list) and len(
                                      annotation_b['classifications']):
                        if isinstance(annotation_b['classifications'][0], list):
                            annotation_b['classifications'] = annotation_b[
                                'classifications'][0]

                    assert annotation_a == annotation_b


# After check the nd serializer on this shit.. It should work for almost everything (except the other horse shit..)
