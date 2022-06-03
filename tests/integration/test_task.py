import pytest

from labelbox import DataRow
from labelbox.schema.data_row_metadata import DataRowMetadataField

EMBEDDING_SCHEMA_ID = "ckpyije740000yxdk81pbgjdc"


def test_task_errors(dataset, image_url):
    client = dataset.client
    embeddings = [0.0] * 128
    task = dataset.create_data_rows([
        {
            DataRow.row_data:
                image_url,
            DataRow.metadata_fields: [
                DataRowMetadataField(schema_id=EMBEDDING_SCHEMA_ID,
                                     value=embeddings),
                DataRowMetadataField(schema_id=EMBEDDING_SCHEMA_ID,
                                     value=embeddings)
            ]
        },
    ])
    assert task in client.get_user().created_tasks()
    task.wait_till_done()
    assert task.status == "FAILED"
    assert task.errors is not None
    assert 'message' in task.errors
    with pytest.raises(Exception) as exc_info:
        task.result
    assert str(exc_info.value).startswith(
        "Job failed. Errors : Failed to validate the metadata")


def test_task_success(dataset, image_url):
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
