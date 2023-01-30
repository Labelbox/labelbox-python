import pytest

from labelbox import DataRow
from labelbox.schema.data_row_metadata import DataRowMetadataField

TEXT_SCHEMA_ID = "cko8s9r5v0001h2dk9elqdidh"


def test_task_errors(dataset, image_url):
    client = dataset.client
    task = dataset.create_data_rows([
        {
            DataRow.row_data:
                image_url,
            DataRow.metadata_fields: [
                DataRowMetadataField(schema_id=TEXT_SCHEMA_ID,
                                     value='some msg'),
                DataRowMetadataField(schema_id=TEXT_SCHEMA_ID,
                                     value='some msg 2')
            ]
        },
    ])

    assert task in client.get_user().created_tasks()
    task.wait_till_done()
    assert task.status == "FAILED"
    assert len(task.failed_data_rows) > 0
    assert task.errors is not None


def test_task_success_json(dataset, image_url):
    client = dataset.client
    task = dataset.create_data_rows([
        {
            DataRow.row_data: image_url,
        },
    ])
    assert task in client.get_user().created_tasks()
    task.wait_till_done()
    assert task.status == "COMPLETE"
    assert task.errors is None
    assert task.result is not None
    assert len(task.result)


def test_task_success_label_export(client, configured_project_with_label):
    project, _, _, _ = configured_project_with_label
    project.export_labels()
    user = client.get_user()
    task = None
    for task in user.created_tasks():
        if task.name != 'JSON Import':
            break

    with pytest.raises(ValueError) as exc_info:
        task.result
    assert str(exc_info.value).startswith("Task result is only supported for")
