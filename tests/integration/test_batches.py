import pytest

from labelbox import Project, Dataset


def test_create_batches(project: Project, big_dataset: Dataset):
    data_rows = [dr.uid for dr in list(big_dataset.export_data_rows())]
    task = project.create_batches("test-batch", data_rows, priority=3)

    task.wait_till_done()
    assert task.errors() is None
    batches = task.result()

    assert len(batches) == 1
    assert batches[0].name == "test-batch0000"
    assert batches[0].size == len(data_rows)


def test_create_batches_from_dataset(project: Project, big_dataset: Dataset):
    data_rows = [dr.uid for dr in list(big_dataset.export_data_rows())]
    project._wait_until_data_rows_are_processed(data_rows, [], 300)

    task = project.create_batches_from_dataset("test-batch",
                                               big_dataset.uid,
                                               priority=3)

    task.wait_till_done()
    assert task.errors() is None
    batches = task.result()

    assert len(batches) == 1
    assert batches[0].name == "test-batch0000"
    assert batches[0].size == len(data_rows)
