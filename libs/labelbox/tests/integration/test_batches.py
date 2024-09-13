from typing import List

import pytest

from labelbox import Project, Dataset


def test_create_batches(project: Project, big_dataset_data_row_ids: List[str]):
    task = project.create_batches(
        "test-batch", big_dataset_data_row_ids, priority=3
    )

    task.wait_till_done()
    assert task.errors() is None
    batches = task.result()

    assert len(batches) == 1
    assert batches[0].name == "test-batch0000"
    assert batches[0].size == len(big_dataset_data_row_ids)


def test_create_batches_from_dataset(project: Project, big_dataset: Dataset):
    export_task = big_dataset.export()
    export_task.wait_till_done()
    stream = export_task.get_buffered_stream()
    data_rows = [dr.json["data_row"]["id"] for dr in stream]
    project._wait_until_data_rows_are_processed(data_rows, [], 300)

    task = project.create_batches_from_dataset(
        "test-batch", big_dataset.uid, priority=3
    )

    task.wait_till_done()
    assert task.errors() is None
    batches = task.result()

    assert len(batches) == 1
    assert batches[0].name == "test-batch0000"
    assert batches[0].size == len(data_rows)
