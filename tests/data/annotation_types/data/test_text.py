import os

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
    text = text_data.value
    assert len(text) == 3541


def test_file(tmpdir):
    content = "foo bar baz"
    file = "hello.txt"
    dir = tmpdir.mkdir('data')
    dir.join(file).write(content)
    text_data = TextData(file_path=os.path.join(dir.strpath, file))
    assert len(text_data.value) == len(content)


def test_ref():
    external_id = "external_id"
    uid = "uid"
    data = TextData(text="hello world", external_id=external_id, uid=uid)
    assert data.external_id == external_id
    assert data.uid == uid
