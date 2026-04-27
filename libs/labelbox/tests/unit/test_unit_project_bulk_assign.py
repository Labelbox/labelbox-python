from unittest.mock import MagicMock

import pytest

from labelbox.schema.project import Project
from labelbox.schema.task_assignment_status import TaskAssignmentStatus


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


def test_bulk_assign_sends_correct_mutation_and_variables(project, mock_client):
    mock_client.execute.return_value = {"bulkAssignDataRows": {"success": True}}
    data_row_ids = ["dr_1", "dr_2", "dr_3"]

    result = project.bulk_assign_data_rows("user_123", data_row_ids)

    assert result is True
    mock_client.execute.assert_called_once()
    args, _ = mock_client.execute.call_args
    query_str, params = args

    assert "BulkAssignDataRowsPyApi" in query_str
    assert "bulkAssignDataRows" in query_str
    assert params == {
        "input": {
            "projectId": "test_project_id",
            "userId": "user_123",
            "dataRowIds": ["dr_1", "dr_2", "dr_3"],
        }
    }


def test_bulk_assign_omits_allowed_statuses_when_none(project, mock_client):
    mock_client.execute.return_value = {"bulkAssignDataRows": {"success": True}}

    project.bulk_assign_data_rows("user_123", ["dr_1"])

    _, params = mock_client.execute.call_args[0]
    assert "allowedStatuses" not in params["input"]


def test_bulk_assign_serializes_allowed_statuses(project, mock_client):
    mock_client.execute.return_value = {"bulkAssignDataRows": {"success": True}}

    project.bulk_assign_data_rows(
        "user_123",
        ["dr_1"],
        allowed_statuses=[
            TaskAssignmentStatus.FREE,
            TaskAssignmentStatus.RESERVED,
        ],
    )

    _, params = mock_client.execute.call_args[0]
    assert params["input"]["allowedStatuses"] == ["FREE", "RESERVED"]


def test_bulk_assign_single_status(project, mock_client):
    mock_client.execute.return_value = {"bulkAssignDataRows": {"success": True}}

    project.bulk_assign_data_rows(
        "user_123",
        ["dr_1"],
        allowed_statuses=[TaskAssignmentStatus.RESERVED],
    )

    _, params = mock_client.execute.call_args[0]
    assert params["input"]["allowedStatuses"] == ["RESERVED"]


def test_bulk_assign_empty_data_rows_returns_true_without_execute(
    project, mock_client
):
    result = project.bulk_assign_data_rows("user_123", [])

    assert result is True
    mock_client.execute.assert_not_called()


def test_bulk_assign_returns_false_on_server_failure(project, mock_client):
    mock_client.execute.return_value = {
        "bulkAssignDataRows": {"success": False}
    }

    result = project.bulk_assign_data_rows("user_123", ["dr_1"])

    assert result is False
