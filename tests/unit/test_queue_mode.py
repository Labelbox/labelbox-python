import pytest

from labelbox.schema.queue_mode import QueueMode


def test_parse_deprecated_catalog():
    assert QueueMode("CATALOG") == QueueMode.Batch


def test_parse_batch():
    assert QueueMode("BATCH") == QueueMode.Batch


def test_parse_data_set():
    assert QueueMode("DATA_SET") == QueueMode.Dataset


def test_fails_for_unknown():
    with pytest.raises(ValueError):
        QueueMode("foo")
