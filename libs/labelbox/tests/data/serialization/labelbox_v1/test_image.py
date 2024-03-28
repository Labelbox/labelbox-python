import json

import pytest

from labelbox.data.serialization.labelbox_v1.converter import LBV1Converter


@pytest.mark.parametrize("file_path", [
    'tests/data/assets/labelbox_v1/highly_nested_image.json',
    'tests/data/assets/labelbox_v1/image_export.json'
])
#TODO: some checklists from the export come in as [checklist ans: []]
# while others are checklist ans: []... when we can figure out why we sometimes
# have extra brackets, we can look into testing nested checklist answers
# and ensuring the export's output matches deserialized/serialized output
def test_image(file_path):
    with open(file_path, 'r') as file:
        payload = json.load(file)

    collection = LBV1Converter.deserialize([payload])
    serialized = next(LBV1Converter.serialize(collection))

    # We are storing the media types now.
    payload['media_type'] = 'image'
    payload['Global Key'] = None

    assert serialized.keys() == payload.keys()

    for key in serialized:
        if key != 'Label':
            assert serialized[key] == payload[key]
        elif key == 'Label':
            for annotation_a, annotation_b in zip(serialized[key]['objects'],
                                                  payload[key]['objects']):
                annotation_b['page'] = None
                annotation_b['unit'] = None
                if not len(annotation_a['classifications']):
                    # We don't add a classification key to the payload if there is no classifications.
                    annotation_a.pop('classifications')

                if isinstance(annotation_b.get('classifications'),
                              list) and len(annotation_b['classifications']):
                    if isinstance(annotation_b['classifications'][0], list):
                        annotation_b['classifications'] = annotation_b[
                            'classifications'][0]
                assert annotation_a == annotation_b


# After check the nd serializer on this shit.. It should work for almost everything (except the other horse shit..)
