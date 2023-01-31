from labelbox_dev.data_row import DataRow
from labelbox_dev.session import Session

from unittest.mock import patch


def test_get_data_rows_by_global_keys(data_rows):
    global_keys = [dr.global_key for dr in data_rows]
    data_rows_iterator = DataRow.get_by_global_keys(global_keys)

    # Test pagination
    data_rows_iterator.limit = 2
    with patch.object(Session, 'get_request',
                      wraps=Session.get_request) as get_request:
        drs = list(data_rows_iterator)
        assert get_request.call_count == 3
    assert len(drs) == 5

    retrived_global_keys = {dr.global_key for dr in drs}
    assert retrived_global_keys == set(global_keys)


def test_get_data_rows_by_ids(data_rows):
    ids = [dr.id for dr in data_rows]
    data_rows_iterator = DataRow.get_by_ids(ids)

    # Test pagination
    data_rows_iterator.limit = 2
    with patch.object(Session, 'get_request',
                      wraps=Session.get_request) as get_request:
        drs = list(data_rows_iterator)
        assert get_request.call_count == 3
    assert len(drs) == 5

    retrived_ids = {dr.id for dr in drs}
    assert retrived_ids == set(ids)
