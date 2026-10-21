from unittest.mock import MagicMock

import pytest
from lbox.exceptions import LabelboxError, ResourceNotFoundError

from labelbox.schema.project import Project


@pytest.fixture
def mock_client():
    return MagicMock()


@pytest.fixture
def project(mock_client):
    return Project(
        mock_client,
        {
            "id": "test_project_id",
            "name": "test",
            "createdAt": "2021-06-01T00:00:00.000Z",
            "updatedAt": "2021-06-01T00:00:00.000Z",
            "autoAuditNumberOfLabels": 1,
            "autoAuditPercentage": 100,
            "dataRowCount": 1,
            "description": "test",
            "editorTaskType": "MODEL_CHAT_EVALUATION",
            "lastActivityTime": "2021-06-01T00:00:00.000Z",
            "allowedMediaType": "IMAGE",
            "setupComplete": "2021-06-01T00:00:00.000Z",
            "modelSetupComplete": None,
            "uploadType": "Auto",
            "isBenchmarkEnabled": False,
            "isConsensusEnabled": False,
        },
    )


def test_clear_queue_reservations_sends_mutation_and_returns_count(
    project, mock_client
):
    mock_client.execute.return_value = {
        "clearQueueReservations": {
            "success": True,
            "clearedReservationCount": 12,
        }
    }

    result = project.clear_queue_reservations("queue_1")

    assert result == 12
    mock_client.execute.assert_called_once()
    query_str, params = mock_client.execute.call_args[0]
    assert "ClearQueueReservationsPyApi" in query_str
    assert "clearedReservationCount" in query_str
    assert params == {
        "input": {"projectId": "test_project_id", "queueId": "queue_1"}
    }


def test_clear_queue_reservations_returns_none_when_count_unknown(
    project, mock_client
):
    mock_client.execute.return_value = {
        "clearQueueReservations": {
            "success": True,
            "clearedReservationCount": None,
        }
    }

    assert project.clear_queue_reservations("queue_1") is None


def test_clear_queue_reservations_raises_on_server_failure(
    project, mock_client
):
    mock_client.execute.return_value = {
        "clearQueueReservations": {
            "success": False,
            "clearedReservationCount": None,
        }
    }

    with pytest.raises(LabelboxError, match="queue_1"):
        project.clear_queue_reservations("queue_1")


def test_clear_queue_reservations_raises_when_queue_not_found(
    project, mock_client
):
    mock_client.execute.side_effect = ResourceNotFoundError(
        message="Task queue not found"
    )

    with pytest.raises(ResourceNotFoundError):
        project.clear_queue_reservations("missing_queue")

    assert (
        mock_client.execute.call_args.kwargs["raise_return_resource_not_found"]
        is True
    )
