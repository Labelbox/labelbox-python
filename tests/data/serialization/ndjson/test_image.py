import json

from labelbox.data.serialization.ndjson.converter import NDJsonConverter


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


def test_image():
    with open('tests/data/assets/ndjson/image_import.json', 'r') as file:
        data = json.load(file)

    res = NDJsonConverter.deserialize(data).as_collection()
    res = list(NDJsonConverter.serialize(res))
    for r in res:
        r.pop('classifications', None)
    assert [round_dict(x) for x in res] == [round_dict(x) for x in data]
