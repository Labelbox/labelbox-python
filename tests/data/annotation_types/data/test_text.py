import pytest
from pydantic import ValidationError

from labelbox.data.annotation_types import TextData

def test_validate_schema():
    with pytest.raises(ValidationError):
        data = TextData()


def test_text():
    text = "hello world"
    text_data = TextData(text=text)
    assert text_data.text == text


def test_url():
    url = "https://filesamples.com/samples/document/txt/sample3.txt"
    text_data = TextData(url=url)
    text = text_data.data
    assert len(text) == 3541


def test_file():
    file_path = "tests/data/assets/sample_text.txt"
    text_data = TextData(file_path=file_path)
    text = text_data.data
    assert len(text) == 3541


def test_ref():
    external_id = "external_id"
    uid = "uid"
    data = TextData(text="hello world", external_id=external_id, uid=uid)
    assert data.external_id == external_id
    assert data.uid == uid
