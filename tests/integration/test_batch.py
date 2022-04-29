import pytest

from labelbox import Dataset, Project
from labelbox.schema.project import QueueMode

IMAGE_URL = "https://storage.googleapis.com/diagnostics-demo-data/coco/COCO_train2014_000000000034.jpg"


@pytest.fixture
def big_dataset(dataset: Dataset):
    task = dataset.create_data_rows([
        {
            "row_data": IMAGE_URL,
            "external_id": "my-image"
        },
    ] * 250)
    task.wait_till_done()

    yield dataset
    dataset.delete()


def test_submit_batch(configured_project: Project, big_dataset):
    configured_project.update(queue_mode=QueueMode.Batch)

    data_rows = [dr.uid for dr in list(big_dataset.export_data_rows())]
    queue_res = configured_project.queue(data_rows)
    assert not len(queue_res)
    dequeue_res = configured_project.dequeue(data_rows)
    assert not len(dequeue_res)
