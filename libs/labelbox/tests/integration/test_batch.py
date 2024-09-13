import time
from typing import List
from uuid import uuid4
import pytest

from labelbox import Dataset, Project
from labelbox.exceptions import (
    ProcessingWaitTimeout,
    MalformedQueryException,
    ResourceConflict,
    LabelboxError,
)


def get_data_row_ids(ds: Dataset):
    return [dr.uid for dr in list(ds.data_rows())]


def test_create_batch(project: Project, big_dataset_data_row_ids: List[str]):
    batch = project.create_batch(
        "test-batch",
        big_dataset_data_row_ids,
        3,
        consensus_settings={"number_of_labels": 3, "coverage_percentage": 0.1},
    )

    assert batch.name == "test-batch"
    assert batch.size == len(big_dataset_data_row_ids)
    assert len([dr for dr in batch.failed_data_row_ids]) == 0


def test_create_batch_with_invalid_data_rows_ids(project: Project):
    with pytest.raises(MalformedQueryException) as ex:
        project.create_batch("test-batch", data_rows=["a", "b", "c"])
        assert (
            str(ex) == "No valid data rows to be added from the list provided!"
        )


def test_create_batch_with_the_same_name(
    project: Project, small_dataset: Dataset
):
    batch1 = project.create_batch(
        "batch1", data_rows=get_data_row_ids(small_dataset)
    )
    assert batch1.name == "batch1"

    with pytest.raises(ResourceConflict):
        project.create_batch(
            "batch1", data_rows=get_data_row_ids(small_dataset)
        )


def test_create_batch_with_same_data_row_ids(
    project: Project, small_dataset: Dataset
):
    batch1 = project.create_batch(
        "batch1", data_rows=get_data_row_ids(small_dataset)
    )
    assert batch1.name == "batch1"

    with pytest.raises(MalformedQueryException) as ex:
        project.create_batch(
            "batch2", data_rows=get_data_row_ids(small_dataset)
        )
        assert str(ex) == "No valid data rows to add to project"


def test_create_batch_with_non_existent_global_keys(project: Project):
    with pytest.raises(MalformedQueryException) as ex:
        project.create_batch("batch1", global_keys=["key1"])
        assert (
            str(ex)
            == "Data rows with the following global keys do not exist: key1."
        )


def test_create_batch_with_string_priority(
    project: Project, small_dataset: Dataset
):
    with pytest.raises(LabelboxError):
        project.create_batch(
            "batch1", data_rows=get_data_row_ids(small_dataset), priority="abcd"
        )


def test_create_batch_with_null_priority(
    project: Project, small_dataset: Dataset
):
    with pytest.raises(LabelboxError):
        project.create_batch(
            "batch1", data_rows=get_data_row_ids(small_dataset), priority=None
        )


def test_create_batch_async(
    project: Project, big_dataset_data_row_ids: List[str]
):
    batch = project._create_batch_async(
        "big-batch", big_dataset_data_row_ids, priority=3
    )
    assert batch.name == "big-batch"
    assert batch.size == len(big_dataset_data_row_ids)
    assert len([dr for dr in batch.failed_data_row_ids]) == 0


def test_create_batch_with_consensus_settings(
    project: Project, small_dataset: Dataset
):
    export_task = small_dataset.export()
    export_task.wait_till_done()
    stream = export_task.get_buffered_stream()
    data_rows = [dr.json["data_row"]["id"] for dr in stream]
    consensus_settings = {"coverage_percentage": 0.1, "number_of_labels": 3}
    batch = project.create_batch(
        "batch with consensus settings",
        data_rows,
        3,
        consensus_settings=consensus_settings,
    )
    assert batch.name == "batch with consensus settings"
    assert batch.size == len(data_rows)
    assert batch.consensus_settings == consensus_settings


def test_create_batch_with_data_row_class(
    project: Project, small_dataset: Dataset
):
    export_task = small_dataset.export()
    export_task.wait_till_done()
    stream = export_task.get_buffered_stream()
    data_rows = [dr.json["data_row"]["id"] for dr in stream]
    batch = project.create_batch("test-batch-data-rows", data_rows, 3)
    assert batch.name == "test-batch-data-rows"
    assert batch.size == len(data_rows)


def test_archive_batch(project: Project, small_dataset: Dataset):
    export_task = small_dataset.export()
    export_task.wait_till_done()
    stream = export_task.get_buffered_stream()
    data_rows = [dr.json["data_row"]["id"] for dr in stream]

    batch = project.create_batch("batch to archive", data_rows)
    batch.remove_queued_data_rows()
    overview = project.get_overview()

    assert overview.to_label == 0


def test_delete(project: Project, small_dataset: Dataset):
    export_task = small_dataset.export()
    export_task.wait_till_done()
    stream = export_task.get_buffered_stream()
    data_rows = [dr.json["data_row"]["id"] for dr in stream]
    batch = project.create_batch("batch to delete", data_rows)
    batch.delete()

    assert len(list(project.batches())) == 0


def test_batch_project(project: Project, small_dataset: Dataset):
    export_task = small_dataset.export()
    export_task.wait_till_done()
    stream = export_task.get_buffered_stream()
    data_rows = [dr.json["data_row"]["id"] for dr in stream]
    batch = project.create_batch(
        "batch to test project relationship", data_rows
    )

    project_from_batch = batch.project()

    assert project_from_batch.uid == project.uid
    assert project_from_batch.name == project.name


def test_batch_creation_for_data_rows_with_issues(
    project: Project,
    small_dataset: Dataset,
    dataset_with_invalid_data_rows: Dataset,
):
    """
    Create a batch containing both valid and invalid data rows
    """
    valid_data_rows = [dr.uid for dr in list(small_dataset.data_rows())]
    invalid_data_rows = [
        dr.uid for dr in list(dataset_with_invalid_data_rows.data_rows())
    ]
    data_rows_to_add = valid_data_rows + invalid_data_rows

    assert len(data_rows_to_add) == 4
    batch = project.create_batch(
        "batch to test failed data rows", data_rows_to_add
    )
    failed_data_row_ids = [x for x in batch.failed_data_row_ids]
    assert len(failed_data_row_ids) == 2

    failed_data_row_ids_set = set(failed_data_row_ids)
    invalid_data_rows_set = set(invalid_data_rows)
    assert len(failed_data_row_ids_set.intersection(invalid_data_rows_set)) == 2


def test_batch_creation_with_processing_timeout(
    project: Project,
    small_dataset: Dataset,
    unique_dataset: Dataset,
    upload_invalid_data_rows_for_dataset,
):
    """
    Create a batch with zero wait time, this means that the waiting logic will throw exception immediately
    """
    #  wait for these data rows to be processed
    valid_data_rows = [dr.uid for dr in list(small_dataset.data_rows())]

    # upload data rows for this dataset and don't wait
    upload_invalid_data_rows_for_dataset(unique_dataset)
    unprocessed_data_rows = [dr.uid for dr in list(unique_dataset.data_rows())]

    data_row_ids = valid_data_rows + unprocessed_data_rows

    stashed_wait_timeout = project._wait_processing_max_seconds
    with pytest.raises(ProcessingWaitTimeout):
        # emulate the situation where there are still some data rows being
        # processed but wait timeout exceeded
        project._wait_processing_max_seconds = 0
        project.create_batch("batch to test failed data rows", data_row_ids)
    project._wait_processing_max_seconds = stashed_wait_timeout


def test_list_all_batches(project: Project, client, image_url: str):
    """
    Test to verify that we can retrieve all available batches in the project.
    """
    # Data to use
    img_assets = [
        {"row_data": image_url, "external_id": str(uuid4())}
        for asset in range(0, 2)
    ]
    data = [img_assets for _ in range(0, 2)]

    # Setup
    batches = []
    datasets = []

    for assets in data:
        dataset = client.create_dataset(name=str(uuid4()))
        create_data_rows_task = dataset.create_data_rows(assets)
        create_data_rows_task.wait_till_done()
        datasets.append(dataset)

    for dataset in datasets:
        data_row_ids = get_data_row_ids(dataset)
        new_batch = project.create_batch(
            name=str(uuid4()), data_rows=data_row_ids
        )
        batches.append(new_batch)

    # Test
    project_batches = list(project.batches())
    assert len(batches) == len(project_batches)

    for project_batch in project_batches:
        for assets in data:
            assert len(assets) == project_batch.size

    # Clean up
    for dataset in datasets:
        dataset.delete()


def test_list_project_batches_with_no_batches(project: Project):
    batches = list(project.batches())
    assert len(batches) == 0


@pytest.mark.skip(
    reason="Test cannot be used effectively with MAL/LabelImport. \
Fix/Unskip after resolving deletion with MAL/LabelImport"
)
def test_delete_labels(project, small_dataset):
    export_task = small_dataset.export()
    export_task.wait_till_done()
    stream = export_task.get_buffered_stream()
    data_rows = [dr.json["data_row"]["id"] for dr in stream]
    batch = project.create_batch("batch to delete labels", data_rows)


@pytest.mark.skip(
    reason="Test cannot be used effectively with MAL/LabelImport. \
Fix/Unskip after resolving deletion with MAL/LabelImport"
)
def test_delete_labels_with_templates(project: Project, small_dataset: Dataset):
    export_task = small_dataset.export()
    export_task.wait_till_done()
    stream = export_task.get_buffered_stream()
    data_rows = [dr.json["data_row"]["id"] for dr in stream]
    batch = project.create_batch(
        "batch to delete labels w templates", data_rows
    )

    export_task = project.export(filters={"batch_ids": [batch.uid]})
    export_task.wait_till_done()
    stream = export_task.get_buffered_stream()
    exported_data_rows = [dr.json["data_row"]["id"] for dr in stream]

    res = batch.delete_labels(labels_as_template=True)

    export_task = project.export(filters={"batch_ids": [batch.uid]})
    export_task.wait_till_done()
    stream = export_task.get_buffered_stream()
    exported_data_rows = [dr.json["data_row"]["id"] for dr in stream]

    assert len(exported_data_rows) == 5
