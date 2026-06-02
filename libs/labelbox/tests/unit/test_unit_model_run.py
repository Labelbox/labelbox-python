from unittest.mock import MagicMock

from lbox.exceptions import LabelboxError

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
    # The model run id is passed to the Foundry query.
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


def test_cost_and_usage_none_for_non_foundry_run():
    client = MagicMock()
    client.execute.side_effect = LabelboxError("model job not found")
    model_run = _make_model_run(client)

    assert model_run.total_cost is None
    assert model_run.total_data_rows is None
