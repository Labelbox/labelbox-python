from unittest.mock import MagicMock

import pytest
from lbox.exceptions import (
    InternalServerError,
    NetworkError,
    ResourceNotFoundError,
)

from labelbox.schema.model_run import ModelRun


def _make_model_run(client):
    return ModelRun(
        client,
        {
            "id": "model-run-1",
            "name": "test run",
            "createdAt": "2021-06-01T00:00:00.000Z",
            "updatedAt": "2021-06-01T00:00:00.000Z",
            "createdBy": "user-1",
            "modelId": "model-1",
            "trainingMetadata": {},
            "modelAppId": "app-1",
        },
    )


def test_total_cost_and_data_rows_are_fetched_and_cached():
    client = MagicMock()
    client.execute.return_value = {
        "modelFoundryModelRunInfo": {
            "cost": 3.5,
            "status": "finished",
            "totalDataRows": 12,
        }
    }
    model_run = _make_model_run(client)

    assert model_run.total_cost == 3.5
    assert model_run.total_data_rows == 12

    # Cost/usage is rehydrated once and cached across property reads.
    assert client.execute.call_count == 1
    # The model run id is passed to the query.
    assert client.execute.call_args[0][1] == {"modelRunId": "model-run-1"}


def test_refresh_cost_and_usage_refetches():
    client = MagicMock()
    client.execute.return_value = {
        "modelFoundryModelRunInfo": {
            "cost": 1.0,
            "status": "finished",
            "totalDataRows": 1,
        }
    }
    model_run = _make_model_run(client)

    assert model_run.total_cost == 1.0
    model_run.refresh_cost_and_usage()
    assert model_run.total_cost == 1.0
    assert client.execute.call_count == 2


@pytest.mark.parametrize(
    "error",
    [
        ResourceNotFoundError(message="model run not found"),
        InternalServerError("no model job for run"),
    ],
)
def test_cost_and_usage_none_for_non_foundry_run(error):
    client = MagicMock()
    client.execute.side_effect = error
    model_run = _make_model_run(client)

    assert model_run.total_cost is None
    assert model_run.total_data_rows is None


@pytest.mark.parametrize(
    "execute_result",
    [
        None,  # execute() can return None instead of a payload
        {"modelFoundryModelRunInfo": None},
    ],
)
def test_cost_and_usage_none_when_payload_missing(execute_result):
    client = MagicMock()
    client.execute.return_value = execute_result
    model_run = _make_model_run(client)

    assert model_run.total_cost is None
    assert model_run.total_data_rows is None


def test_transient_errors_propagate_and_are_not_cached():
    client = MagicMock()
    client.execute.side_effect = NetworkError(Exception("boom"))
    model_run = _make_model_run(client)

    with pytest.raises(NetworkError):
        _ = model_run.total_cost

    # The failure is not cached, so a later successful access recovers.
    client.execute.side_effect = None
    client.execute.return_value = {
        "modelFoundryModelRunInfo": {
            "cost": 2.0,
            "status": "finished",
            "totalDataRows": 5,
        }
    }
    assert model_run.total_cost == 2.0
    assert model_run.total_data_rows == 5
