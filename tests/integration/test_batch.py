import pytest

from labelbox import Dataset, Project
from labelbox.schema.queue_mode import QueueMode

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


@pytest.fixture
def small_dataset(dataset: Dataset):
    task = dataset.create_data_rows([
        {
            "row_data": IMAGE_URL,
            "external_id": "my-image"
        },
    ] * 3)
    task.wait_till_done()

    yield dataset


def test_create_batch(configured_project: Project, big_dataset: Dataset):
    configured_project.update(queue_mode=QueueMode.Batch)

    data_rows = [dr.uid for dr in list(big_dataset.export_data_rows())]
    batch = configured_project.create_batch("test-batch", data_rows, 3)
    assert batch.name == "test-batch"
    assert batch.size == len(data_rows)


def test_archive_batch(configured_project: Project, small_dataset: Dataset):
    data_rows = [dr.uid for dr in list(small_dataset.export_data_rows())]
    configured_project.update(queue_mode=QueueMode.Batch)
    batch = configured_project.create_batch("batch to archive", data_rows)
    batch.remove_queued_data_rows()
    exported_data_rows = list(batch.export_data_rows())

    assert len(exported_data_rows) == 0


def test_delete(configured_project: Project, small_dataset: Dataset):
    data_rows = [dr.uid for dr in list(small_dataset.export_data_rows())]
    configured_project.update(queue_mode=QueueMode.Batch)
    batch = configured_project.create_batch("batch to delete", data_rows)
    batch.delete()

    assert len(list(configured_project.batches())) == 0


def test_batch_project(configured_project: Project, small_dataset: Dataset):
    data_rows = [dr.uid for dr in list(small_dataset.export_data_rows())]
    configured_project.update(queue_mode=QueueMode.Batch)
    batch = configured_project.create_batch(
        "batch to test project relationship", data_rows)
    project_from_batch = batch.project()

    assert project_from_batch.uid == configured_project.uid
    assert project_from_batch.name == configured_project.name


def test_export_data_rows(configured_project: Project, dataset: Dataset):
    n_data_rows = 5
    task = dataset.create_data_rows([
        {
            "row_data": IMAGE_URL,
            "external_id": "my-image"
        },
    ] * n_data_rows)
    task.wait_till_done()

    data_rows = [dr.uid for dr in list(dataset.export_data_rows())]
    configured_project.update(queue_mode=QueueMode.Batch)
    batch = configured_project.create_batch("batch test", data_rows)

    result = list(batch.export_data_rows())
    exported_data_rows = [dr.uid for dr in result]

    assert len(result) == n_data_rows
    assert set(data_rows) == set(exported_data_rows)


@pytest.mark.skip(
    reason="Test cannot be used effectively with MAL/LabelImport. \
Fix/Unskip after resolving deletion with MAL/LabelImport")
def test_delete_labels(configured_project_with_label):
    project, dataset, _, _ = configured_project_with_label

    data_rows = [dr.uid for dr in list(dataset.export_data_rows())]
    project.update(queue_mode=QueueMode.Batch)
    batch = project.create_batch("batch to delete labels", data_rows)


@pytest.mark.skip(
    reason="Test cannot be used effectively with MAL/LabelImport. \
Fix/Unskip after resolving deletion with MAL/LabelImport")
def test_delete_labels_with_templates(configured_project: Project,
                                      small_dataset: Dataset):
    data_rows = [dr.uid for dr in list(small_dataset.export_data_rows())]
    configured_project.update(queue_mode=QueueMode.Batch)
    batch = configured_project.create_batch(
        "batch to delete labels w templates", data_rows)
    exported_data_rows = list(batch.export_data_rows())
    res = batch.delete_labels(labels_as_template=True)
    exported_data_rows = list(batch.export_data_rows())
    assert len(exported_data_rows) == 5
