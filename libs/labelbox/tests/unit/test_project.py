import pytest
from unittest.mock import MagicMock

from labelbox.schema.project import Project
from labelbox.schema.ontology_kind import EditorTaskType


@pytest.mark.parametrize(
    'api_editor_task_type, expected_editor_task_type',
    [(None, EditorTaskType.Missing),
     ('MODEL_CHAT_EVALUATION', EditorTaskType.ModelChatEvaluation),
     ('RESPONSE_CREATION', EditorTaskType.ResponseCreation),
     ('OFFLINE_MODEL_CHAT_EVALUATION',
      EditorTaskType.OfflineModelChatEvaluation),
     ('NEW_TYPE', EditorTaskType.Missing)])
def test_project_editor_task_type(api_editor_task_type,
                                  expected_editor_task_type):
    client = MagicMock()
    project = Project(
        client, {
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
            "queueMode": "BATCH",
            "setupComplete": "2021-06-01T00:00:00.000Z",
        })

    assert project.editor_task_type == expected_editor_task_type
