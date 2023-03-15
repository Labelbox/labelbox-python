import json

from labelbox.data.serialization.ndjson.converter import NDJsonConverter


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


def test_pdf_document_entity():
    """
    Tests a pdf file with bbox annotations only
    """
    with open('tests/data/assets/ndjson/pdf_document_entity_import.json',
              'r') as f:
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
