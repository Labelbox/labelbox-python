import json

from labelbox.data.serialization.ndjson.converter import NDJsonConverter


def test_video():
    with open('tests/data/assets/ndjson/video_import.json', 'r') as file:
        data = json.load(file)

    res = NDJsonConverter.deserialize(data)
    res.data = list(res.data)
    res = list(NDJsonConverter.serialize(res))
    assert res == [data[2], data[0], data[1]]
