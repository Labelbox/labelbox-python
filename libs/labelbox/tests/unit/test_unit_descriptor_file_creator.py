import json

from unittest.mock import MagicMock, Mock
import pytest

from labelbox.schema.internal.descriptor_file_creator import DescriptorFileCreator


def test_chunk_down_by_bytes_row_too_large():
    client = MagicMock()

    descriptor_file_creator = DescriptorFileCreator(client)

    chunk = [{"row_data": "a"}]
    max_chunk_size_bytes = 1

    with pytest.raises(ValueError):
        res = descriptor_file_creator._chunk_down_by_bytes(
            chunk, max_chunk_size_bytes)
        [x for x in res]


def test_chunk_down_by_bytes_more_chunks():
    client = MagicMock()

    descriptor_file_creator = DescriptorFileCreator(client)

    chunk = [{"row_data": "a"}, {"row_data": "b"}]
    max_chunk_size_bytes = json.dumps(chunk).__sizeof__() - 1

    res = descriptor_file_creator._chunk_down_by_bytes(chunk,
                                                       max_chunk_size_bytes)
    assert [x for x in res] == [
        json.dumps([{
            "row_data": "a"
        }]), json.dumps([{
            "row_data": "b"
        }])
    ]


def test_chunk_down_by_bytes_one_chunk():
    client = MagicMock()

    descriptor_file_creator = DescriptorFileCreator(client)

    chunk = [{"row_data": "a"}, {"row_data": "b"}]
    max_chunk_size_bytes = json.dumps(chunk).__sizeof__()

    res = descriptor_file_creator._chunk_down_by_bytes(chunk,
                                                       max_chunk_size_bytes)
    assert [x for x in res
           ] == [json.dumps([{
               "row_data": "a"
           }, {
               "row_data": "b"
           }])]
