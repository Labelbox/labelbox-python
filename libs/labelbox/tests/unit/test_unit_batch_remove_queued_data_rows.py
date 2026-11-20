from unittest.mock import MagicMock

import pytest

from labelbox.schema.batch import Batch


@pytest.fixture
def mock_client():
    return MagicMock()


@pytest.fixture
def batch(mock_client):
    return Batch(
        mock_client,
        "test_project_id",
        {
            "id": "test_batch_id",
            "name": "test",
            "createdAt": "2021-06-01T00:00:00.000Z",
            "updatedAt": "2021-06-01T00:00:00.000Z",
            "size": 3,
            "consensusSettingsJson": None,
        },
    )


def test_without_ids_removes_every_queued_row(batch, mock_client):
    batch.remove_queued_data_rows()

    query, params = mock_client.execute.call_args.args
    assert "dataRowIds" not in query
    assert params == {
        "projectId": "test_project_id",
        "batchId": "test_batch_id",
    }
    assert mock_client.execute.call_args.kwargs == {"experimental": True}


def test_with_ids_sends_only_those_ids(batch, mock_client):
    batch.remove_queued_data_rows(data_row_ids=("dr_1", "dr_2"))

    query, params = mock_client.execute.call_args.args
    assert (
        "removeQueuedDataRowsFromBatch(batchId: $batchId, dataRowIds: $dataRowIds)"
        in query
    )
    assert params == {
        "projectId": "test_project_id",
        "batchId": "test_batch_id",
        "dataRowIds": ["dr_1", "dr_2"],
    }
    assert mock_client.execute.call_args.kwargs == {"experimental": True}


def test_one_shot_iterable_of_ids_is_sent_in_full(batch, mock_client):
    batch.remove_queued_data_rows(
        data_row_ids=(data_row_id for data_row_id in ["dr_1", "dr_2"])
    )

    _, params = mock_client.execute.call_args.args
    assert params["dataRowIds"] == ["dr_1", "dr_2"]


def test_empty_ids_are_rejected_before_any_request(batch, mock_client):
    with pytest.raises(ValueError, match="must not be empty"):
        batch.remove_queued_data_rows(data_row_ids=[])

    mock_client.execute.assert_not_called()


@pytest.mark.parametrize("bad_ids", ["dr_1", ["dr_1", 2]])
def test_non_list_of_ids_is_rejected(batch, mock_client, bad_ids):
    with pytest.raises(ValueError, match="list of data row ids"):
        batch.remove_queued_data_rows(data_row_ids=bad_ids)

    mock_client.execute.assert_not_called()
