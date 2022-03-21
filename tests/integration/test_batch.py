import pytest

from labelbox import Dataset, Project

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


def test_create_batch(configured_project: Project, big_dataset: Dataset):
    configured_project.update(queue_mode=Project.QueueMode.Batch)

    data_rows = [dr.uid for dr in list(big_dataset.export_data_rows())]
    batch = configured_project.create_batch("test-batch", data_rows, 3)
    assert batch.name == 'test-batch'
    assert batch.size == len(data_rows)
