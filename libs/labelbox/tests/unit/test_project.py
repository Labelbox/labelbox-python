import pytest
from unittest.mock import MagicMock

from labelbox.schema.project import Project, _validate_batch_ids
from labelbox.schema.ontology_kind import EditorTaskType


@pytest.fixture
def project_entity():
    return Project(
        MagicMock(),
        {
            "id": "test",
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


def _workstream_state_counts_response():
    return {
        "workstreamStateCounts": [
            {"state": "Unlabeled", "count": 10},
            {"state": "InReview", "count": 2},
            {"state": "InRework", "count": 1},
            {"state": "Skipped", "count": 0},
            {"state": "Done", "count": 5},
            {"state": "Labeled", "count": 8},
            {"state": "All", "count": 18},
            {"state": "NotInTaskQueue", "count": 3},
        ],
        "taskQueues": [],
        "issues": {"totalCount": 4},
        "completedDataRowCount": 5,
    }


def test_get_overview_project_wide(project_entity):
    client = project_entity.client
    client.execute.return_value = {
        "project": _workstream_state_counts_response()
    }

    overview = project_entity.get_overview()

    assert overview.to_label == 10
    assert overview.total_data_rows == 18
    assert overview.issues == 4

    args, kwargs = client.execute.call_args
    variables = args[1]
    assert variables["projectId"] == "test"
    assert variables["batchIds"] is None
    assert variables["countInput"] is None
    assert variables["includeIssues"] is True
    assert kwargs["experimental"] is True
    query = args[0]
    assert "issues @include(if: $includeIssues)" in query


def test_get_overview_batch_scoped(project_entity):
    client = project_entity.client
    client.execute.return_value = {
        "project": _workstream_state_counts_response()
    }

    overview = project_entity.get_overview(batch_ids=["batch-1"])

    assert overview.issues is None

    args, kwargs = client.execute.call_args
    variables = args[1]
    assert variables["batchIds"] == ["batch-1"]
    assert variables["includeIssues"] is False
    assert variables["countInput"] == {
        "searchQuery": {
            "scope": {"projectId": "test"},
            "query": [{"ids": ["batch-1"], "operator": "is", "type": "batch"}],
        }
    }


@pytest.mark.parametrize(
    "batch_ids,expected_message",
    [
        ([], "batch_ids filter expects a non-empty list."),
        (
            ["batch-1"] * 1001,
            "batch_ids filter only supports a max of 1000 items.",
        ),
    ],
)
def test_validate_batch_ids_rejects_invalid(batch_ids, expected_message):
    with pytest.raises(ValueError, match=expected_message):
        _validate_batch_ids(batch_ids)


def test_get_overview_rejects_empty_batch_ids(project_entity):
    with pytest.raises(
        ValueError, match="batch_ids filter expects a non-empty list."
    ):
        project_entity.get_overview(batch_ids=[])


@pytest.mark.parametrize(
    "api_editor_task_type, expected_editor_task_type",
    [
        (None, EditorTaskType.Missing),
        ("MODEL_CHAT_EVALUATION", EditorTaskType.ModelChatEvaluation),
        ("RESPONSE_CREATION", EditorTaskType.ResponseCreation),
        (
            "OFFLINE_MODEL_CHAT_EVALUATION",
            EditorTaskType.OfflineModelChatEvaluation,
        ),
        ("NEW_TYPE", EditorTaskType.Missing),
    ],
)
def test_project_editor_task_type(
    api_editor_task_type, expected_editor_task_type, project_entity
):
    client = MagicMock()
    project = Project(
        client,
        {
            "id": "test",
            "name": "test",
            "createdAt": "2021-06-01T00:00:00.000Z",
            "updatedAt": "2021-06-01T00:00:00.000Z",
            "autoAuditNumberOfLabels": 1,
            "autoAuditPercentage": 100,
            "dataRowCount": 1,
            "description": "test",
            "editorTaskType": api_editor_task_type,
            "lastActivityTime": "2021-06-01T00:00:00.000Z",
            "allowedMediaType": "IMAGE",
            "setupComplete": "2021-06-01T00:00:00.000Z",
            "modelSetupComplete": None,
            "uploadType": "Auto",
            "isBenchmarkEnabled": False,
            "isConsensusEnabled": False,
        },
    )

    assert project.editor_task_type == expected_editor_task_type
