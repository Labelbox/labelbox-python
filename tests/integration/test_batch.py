import warnings

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


@pytest.fixture(scope='function')
def dataset_with_invalid_data_rows(unique_dataset: Dataset):
    upload_invalid_data_rows_for_dataset(unique_dataset)

    yield unique_dataset


def upload_invalid_data_rows_for_dataset(dataset: Dataset):
    task = dataset.create_data_rows([
        {
            "row_data": 'https://jakub-da-test-primary.s3.us-east-2.amazonaws.com/dogecoin-whitepaper.pdf',
            "external_id": "my-pdf"
        },
    ] * 2)
    task.wait_till_done()


def test_create_batch(batch_project: Project, big_dataset: Dataset):
    data_rows = [dr.uid for dr in list(big_dataset.export_data_rows())]
    batch = batch_project.create_batch("test-batch", data_rows, 3)
    assert batch.name == "test-batch"
    assert batch.size == len(data_rows)


def test_archive_batch(batch_project: Project, small_dataset: Dataset):
    data_rows = [dr.uid for dr in list(small_dataset.export_data_rows())]
    batch = batch_project.create_batch("batch to archive", data_rows)
    batch.remove_queued_data_rows()
    exported_data_rows = list(batch.export_data_rows())

    assert len(exported_data_rows) == 0


def test_delete(batch_project: Project, small_dataset: Dataset):
    data_rows = [dr.uid for dr in list(small_dataset.export_data_rows())]
    batch = batch_project.create_batch("batch to delete", data_rows)
    batch.delete()

    assert len(list(batch_project.batches())) == 0


def test_batch_project(batch_project: Project, small_dataset: Dataset):
    data_rows = [dr.uid for dr in list(small_dataset.export_data_rows())]
    batch = batch_project.create_batch("batch to test project relationship",
                                       data_rows)

    project_from_batch = batch.project()

    assert project_from_batch.uid == batch_project.uid
    assert project_from_batch.name == batch_project.name


def test_batch_creation_for_data_rows_with_issues(
    batch_project: Project,
    small_dataset: Dataset,
    dataset_with_invalid_data_rows: Dataset
):
    """
    Create a batch containing both valid and invalid data rows
    """
    valid_data_rows = [dr.uid for dr in list(small_dataset.export_data_rows())]
    invalid_data_rows = [dr.uid for dr in list(
        dataset_with_invalid_data_rows.export_data_rows())]
    data_rows_to_add = valid_data_rows + invalid_data_rows

    assert len(data_rows_to_add) == 5
    batch = batch_project.create_batch(
        "batch to test failed data rows",
        data_rows_to_add
    )

    assert len(batch.failed_data_row_ids) == 2

    failed_data_row_ids_set = set(batch.failed_data_row_ids)
    invalid_data_rows_set = set(invalid_data_rows)
    assert len(failed_data_row_ids_set.intersection(
        invalid_data_rows_set)) == 2


def test_batch_creation_with_processing_timeout(
    batch_project: Project,
    small_dataset: Dataset,
    unique_dataset: Dataset
):
    """
    Create a batch with zero wait time, this means that the waiting will termintate instantly
    """
    #  wait for these data rows to be processed
    valid_data_rows = [dr.uid for dr in list(small_dataset.export_data_rows())]
    batch_project._wait_until_data_rows_are_processed(
        valid_data_rows, wait_processing_max_seconds=3600, sleep_interval=5
    )

    # upload data rows for this dataset and don't wait
    upload_invalid_data_rows_for_dataset(unique_dataset)
    unprocessed_data_rows = [dr.uid for dr in list(
        unique_dataset.export_data_rows())]

    data_row_ids = valid_data_rows + unprocessed_data_rows
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        breakpoint()
        batch_project.create_batch(
            "batch to test failed data rows",
            data_row_ids,
            wait_processing_max_seconds=0
        )
        assert len(w) == 1
        assert issubclass(w[-1].category, DeprecationWarning)
        assert "Not all data rows have been processed, proceeding anyway" in str(
            w[-1].message)


def test_export_data_rows(batch_project: Project, dataset: Dataset):
    n_data_rows = 5
    task = dataset.create_data_rows([
        {
            "row_data": IMAGE_URL,
            "external_id": "my-image"
        },
    ] * n_data_rows)
    task.wait_till_done()

    data_rows = [dr.uid for dr in list(dataset.export_data_rows())]
    batch = batch_project.create_batch("batch test", data_rows)

    result = list(batch.export_data_rows())
    exported_data_rows = [dr.uid for dr in result]

    assert len(result) == n_data_rows
    assert set(data_rows) == set(exported_data_rows)


@pytest.mark.skip(
    reason="Test cannot be used effectively with MAL/LabelImport. \
Fix/Unskip after resolving deletion with MAL/LabelImport")
def test_delete_labels(batch_project, small_dataset):
    data_rows = [dr.uid for dr in list(small_dataset.export_data_rows())]
    batch = batch_project.create_batch("batch to delete labels", data_rows)


@pytest.mark.skip(
    reason="Test cannot be used effectively with MAL/LabelImport. \
Fix/Unskip after resolving deletion with MAL/LabelImport")
def test_delete_labels_with_templates(batch_project: Project,
                                      small_dataset: Dataset):
    data_rows = [dr.uid for dr in list(small_dataset.export_data_rows())]
    batch = batch_project.create_batch("batch to delete labels w templates",
                                       data_rows)
    exported_data_rows = list(batch.export_data_rows())
    res = batch.delete_labels(labels_as_template=True)
    exported_data_rows = list(batch.export_data_rows())
    assert len(exported_data_rows) == 5
