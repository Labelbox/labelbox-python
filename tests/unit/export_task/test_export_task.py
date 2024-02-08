from unittest import mock
from unittest.mock import MagicMock
import pytest
from labelbox.schema.export_task import ExportTask
from labelbox.schema.task import Task


@pytest.fixture
def export_task():
    client = MagicMock()
    task = Task(
        client, {
            "id": "clscg9qsq00o1071v0ao491zm",
            "completionPercentage": 100,
            "status": "IN_PROGRESS",
            "createdAt": "2021-08-25T20:00:00.000Z",
            "updatedAt": "2021-08-25T20:00:00.000Z",
            "errors": [],
            "metadata": {},
            "name": "TestExportDataRow:test_with_data_row_object",
            "result": None,
            "type": "export-data-rows-streamable",
        })
    return ExportTask(task)


@pytest.fixture
def export_task_complete(export_task):
    export_task._task.status = "COMPLETE"
    return export_task


@pytest.fixture
def export_task_failed(export_task):
    export_task._task.status = "FAILED"
    return export_task


def test_wait_till_done_complete(export_task_complete):
    export_task_complete.wait_till_done()
    assert export_task_complete.status == "COMPLETE"


def test_wait_till_done_failed(export_task_failed):
    export_task_failed.wait_till_done()
    assert export_task_failed.status == "FAILED"
