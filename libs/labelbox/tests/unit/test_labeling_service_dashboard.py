from unittest.mock import MagicMock

from labelbox.schema.labeling_service_dashboard import LabelingServiceDashboard


def test_no_tasks_remaining_count():
    labeling_service_dashboard_data = {
        "id": "cm0eeo4c301lg07061phfhva0",
        "name": "TestStatus",
        "boostRequestedAt": "2024-08-28T22:08:07.446Z",
        "boostUpdatedAt": "2024-08-28T22:08:07.446Z",
        "boostRequestedBy": None,
        "boostStatus": "SET_UP",
        "dataRowsCount": 0,
        "dataRowsDoneCount": 0,
        "dataRowsInReviewCount": 0,
        "dataRowsInReworkCount": 0,
        "tasksTotalCount": 0,
        "tasksCompletedCount": 0,
        "tasksRemainingCount": 0,
        "mediaType": "image",
        "editorTaskType": None,
        "tags": [],
        "client": MagicMock(),
    }
    lsd = LabelingServiceDashboard(**labeling_service_dashboard_data)
    assert lsd.tasks_remaining_count is None


def test_tasks_remaining_count_exists():
    labeling_service_dashboard_data = {
        "id": "cm0eeo4c301lg07061phfhva0",
        "name": "TestStatus",
        "boostRequestedAt": "2024-08-28T22:08:07.446Z",
        "boostUpdatedAt": "2024-08-28T22:08:07.446Z",
        "boostRequestedBy": None,
        "boostStatus": "SET_UP",
        "dataRowsCount": 0,
        "dataRowsDoneCount": 0,
        "dataRowsInReviewCount": 0,
        "dataRowsInReworkCount": 0,
        "tasksTotalCount": 0,
        "tasksCompletedCount": 0,
        "tasksRemainingCount": 1,
        "mediaType": "image",
        "editorTaskType": None,
        "tags": [],
        "client": MagicMock(),
    }
    lsd = LabelingServiceDashboard(**labeling_service_dashboard_data)
    assert lsd.tasks_remaining_count == 1


def test_tasks_total_no_tasks_remaining_count():
    labeling_service_dashboard_data = {
        "id": "cm0eeo4c301lg07061phfhva0",
        "name": "TestStatus",
        "boostRequestedAt": "2024-08-28T22:08:07.446Z",
        "boostUpdatedAt": "2024-08-28T22:08:07.446Z",
        "boostRequestedBy": None,
        "boostStatus": "SET_UP",
        "dataRowsCount": 0,
        "dataRowsDoneCount": 0,
        "dataRowsInReviewCount": 1,
        "dataRowsInReworkCount": 0,
        "tasksTotalCount": 1,
        "tasksCompletedCount": 0,
        "tasksRemainingCount": 0,
        "mediaType": "image",
        "editorTaskType": None,
        "tags": [],
        "client": MagicMock(),
    }
    lsd = LabelingServiceDashboard(**labeling_service_dashboard_data)
    assert lsd.tasks_remaining_count == 0
