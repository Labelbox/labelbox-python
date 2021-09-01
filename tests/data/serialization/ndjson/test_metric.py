import json

from labelbox.data.serialization.labelbox_v1.converter import LBV1Converter
from labelbox.data.serialization.ndjson.converter import NDJsonConverter


def test_metric():
    with open('tests/data/assets/ndjson/metric_import.json', 'r') as file:
        data = json.load(file)

    label_list = NDJsonConverter.deserialize(data).as_list()
    reserialized = list(NDJsonConverter.serialize(label_list))
    assert reserialized == data

    # Just make sure that this doesn't break
    list(LBV1Converter.serialize(label_list))


def test_metric():
    with open('tests/data/assets/ndjson/custom_scalar_import.json',
              'r') as file:
        data = json.load(file)

    label_list = NDJsonConverter.deserialize(data).as_list()
    reserialized = list(NDJsonConverter.serialize(label_list))
    assert reserialized == data

    # Just make sure that this doesn't break
    list(LBV1Converter.serialize(label_list))
