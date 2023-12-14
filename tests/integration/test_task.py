import json
import pytest
import collections.abc
from labelbox import DataRow
from labelbox.schema.data_row_metadata import DataRowMetadataField
from utils import INTEGRATION_SNAPSHOT_DIRECTORY

TEXT_SCHEMA_ID = "cko8s9r5v0001h2dk9elqdidh"


def test_task_errors(dataset, image_url, snapshot):
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

    assert len(task.failed_data_rows) == 1
    assert "A schemaId can only be specified once per DataRow : [cko8s9r5v0001h2dk9elqdidh]" in task.failed_data_rows[
        0]['message']
    assert len(task.failed_data_rows[0]['failedDataRows'][0]['metadata']) == 2


def test_task_success_json(dataset, image_url, snapshot):
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
    assert isinstance(task.result, collections.abc.Sequence)
    assert task.result_url is not None
    assert isinstance(task.result_url, str)
    task_result = task.result[0]
    assert 'id' in task_result and isinstance(task_result['id'], str)
    assert 'row_data' in task_result and isinstance(task_result['row_data'],
                                                    str)
    snapshot.snapshot_dir = INTEGRATION_SNAPSHOT_DIRECTORY
    task_result['id'] = 'DUMMY_ID'
    task_result['row_data'] = 'https://dummy.url'
    snapshot.assert_match(json.dumps(task_result),
                          'test_task.test_task_success_json.json')
    assert len(task.result)


def test_task_success_label_export(client, configured_project_with_label):
    project, _, _, _ = configured_project_with_label
    # TODO: Move to export_v2
    project.export_labels()
    user = client.get_user()
    task = None
    for task in user.created_tasks():
        if task.name != 'JSON Import':
            break

    with pytest.raises(ValueError) as exc_info:
        task.result
    assert str(exc_info.value).startswith("Task result is only supported for")
