import json
from typing import Dict, Any

from labelbox.data.serialization.labelbox_v1.converter import LBV1Converter

IGNORE_KEYS = [
    "Data Split", "media_type", "DataRow Metadata", "Media Attributes"
]


def round_dict(data: Dict[str, Any]) -> Dict[str, Any]:
    for key in data:
        if isinstance(data[key], float):
            data[key] = int(data[key])
        elif isinstance(data[key], dict):
            data[key] = round_dict(data[key])
    return data


def test_pdf():
    """
    Tests an export from a pdf document with only bounding boxes
    """
    payload = json.load(
        open('tests/data/assets/labelbox_v1/pdf_export.json', 'r'))
    collection = LBV1Converter.deserialize(payload)
    serialized = next(LBV1Converter.serialize(collection))

    payload = payload[0]  # only one document in the export

    serialized = {k: v for k, v in serialized.items() if k not in IGNORE_KEYS}

    assert serialized.keys() == payload.keys()
    for key in payload.keys():
        if key == 'Label':
            serialized_no_classes = [{
                k: v for k, v in dic.items() if k != 'classifications'
            } for dic in serialized[key]['objects']]
            serialized_round = [
                round_dict(dic) for dic in serialized_no_classes
            ]
            payload_round = [round_dict(dic) for dic in payload[key]['objects']]
            assert payload_round == serialized_round
        else:
            assert serialized[key] == payload[key]
