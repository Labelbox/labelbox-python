import json
from labelbox.data.serialization.ndjson.label import NDLabel
from labelbox.data.serialization.ndjson.objects import NDDocumentRectangle
import pytest


def test_bad_annotation_input():
    data = [{"test": 3}]
    with pytest.raises(ValueError):
        NDLabel(**{"annotations": data})


def test_correct_annotation_input():
    with open("tests/data/assets/ndjson/pdf_import_name_only.json", "r") as f:
        data = json.load(f)
    assert isinstance(
        NDLabel(**{"annotations": [data[0]]}).annotations[0],
        NDDocumentRectangle,
    )
