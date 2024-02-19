import os

import pytest

from labelbox.data.annotation_types import TextData
from labelbox import pydantic_compat


def test_validate_schema():
    with pytest.raises(pydantic_compat.ValidationError):
        data = TextData()


def test_text():
    text = "hello world"
    metadata = []
    media_attributes = {}
    text_data = TextData(text=text,
                         metadata=metadata,
                         media_attributes=media_attributes)
    assert text_data.text == text


def test_url():
    url = "https://storage.googleapis.com/lb-artifacts-testing-public/sdk_integration_test/sample3.txt"
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
    metadata = []
    media_attributes = {}
    data = TextData(text="hello world",
                    external_id=external_id,
                    uid=uid,
                    metadata=metadata,
                    media_attributes=media_attributes)
    assert data.external_id == external_id
    assert data.uid == uid
    assert data.media_attributes == media_attributes
    assert data.metadata == metadata
