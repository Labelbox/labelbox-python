from unittest.mock import MagicMock

import pytest

from labelbox.schema.export_filters import build_filters


def test_ids_filter():
    client = MagicMock()
    filters = {"data_row_ids": ["id1", "id2"], "batch_ids": ["b1", "b2"]}
    assert build_filters(client, filters) == [{
        "ids": ["id1", "id2"],
        "operator": "is",
        "type": "data_row_id",
    }, {
        "ids": ["b1", "b2"],
        "operator": "is",
        "type": "batch",
    }]


def test_ids_empty_filter():
    client = MagicMock()
    filters = {"data_row_ids": [], "batch_ids": ["b1", "b2"]}
    with pytest.raises(ValueError,
                       match="data_row_id filter expects a non-empty list."):
        build_filters(client, filters)


def test_global_keys_filter():
    client = MagicMock()
    filters = {"global_keys": ["id1", "id2"]}
    assert build_filters(client, filters) == [{
        "ids": ["id1", "id2"],
        "operator": "is",
        "type": "global_key",
    }]


def test_validations():
    client = MagicMock()
    filters = {
        "global_keys": ["id1", "id2"],
        "data_row_ids": ["id1", "id2"],
    }
    with pytest.raises(
            ValueError,
            match=
            "data_rows and global_keys cannot both be present in export filters"
    ):
        build_filters(client, filters)
