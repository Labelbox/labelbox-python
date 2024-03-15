import json
import pytest

from labelbox.data.serialization.ndjson.classification import NDRadio

from labelbox.data.serialization.ndjson.converter import NDJsonConverter
from labelbox.data.serialization.ndjson.objects import NDLine


def round_dict(data):
    if isinstance(data, dict):
        for key in data:
            if isinstance(data[key], float):
                data[key] = int(data[key])
            elif isinstance(data[key], dict):
                data[key] = round_dict(data[key])
            elif isinstance(data[key], (list, tuple)):
                data[key] = [round_dict(r) for r in data[key]]

    return data


@pytest.mark.parametrize('filename', [
    'tests/data/assets/ndjson/classification_import_global_key.json',
    'tests/data/assets/ndjson/metric_import_global_key.json',
    'tests/data/assets/ndjson/polyline_import_global_key.json',
    'tests/data/assets/ndjson/text_entity_import_global_key.json',
    'tests/data/assets/ndjson/conversation_entity_import_global_key.json',
])
def test_many_types(filename: str):
    with open(filename, 'r') as f:
        data = json.load(f)
    res = list(NDJsonConverter.deserialize(data))
    res = list(NDJsonConverter.serialize(res))
    assert res == data
    f.close()


def test_image():
    with open('tests/data/assets/ndjson/image_import_global_key.json',
              'r') as f:
        data = json.load(f)
    res = list(NDJsonConverter.deserialize(data))
    res = list(NDJsonConverter.serialize(res))
    for r in res:
        r.pop('classifications', None)
    assert [round_dict(x) for x in res] == [round_dict(x) for x in data]
    f.close()


def test_pdf():
    with open('tests/data/assets/ndjson/pdf_import_global_key.json', 'r') as f:
        data = json.load(f)
    res = list(NDJsonConverter.deserialize(data))
    res = list(NDJsonConverter.serialize(res))
    assert [round_dict(x) for x in res] == [round_dict(x) for x in data]
    f.close()


def test_video():
    with open('tests/data/assets/ndjson/video_import_global_key.json',
              'r') as f:
        data = json.load(f)

    res = list(NDJsonConverter.deserialize(data))
    res = list(NDJsonConverter.serialize(res))
    assert res == [data[2], data[0], data[1], data[3], data[4], data[5]]
    f.close()
