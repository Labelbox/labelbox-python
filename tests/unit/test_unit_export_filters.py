from unittest.mock import MagicMock

from labelbox.schema.export_filters import build_filters


def test_ids_filter():
    client = MagicMock()
    filters = {"data_row_ids": ["id1", "id2"], "batch_ids": ["b1", "b2"]}
    assert build_filters(client, filters) == [{
        "ids": ["id1", "id2"],
        "operator": "is",
        "type": "data_row_id",
    },
    {
        "ids": ["b1", "b2"],
        "operator": "is",
        "type": "batch",
    }]


def test_global_keys_filter():
    client = MagicMock()
    filters = {"global_keys": ["id1", "id2"]}
    assert build_filters(client, filters) == [{
        "ids": ["id1", "id2"],
        "operator": "is",
        "type": "global_key",
    }]
