import json
import time

import pytest
import requests
import os

from labelbox import Label


def test_labels(configured_project_with_label):
    project, _, data_row, label = configured_project_with_label

    assert list(project.labels()) == [label]
    assert list(data_row.labels()) == [label]

    assert label.project() == project
    assert label.data_row() == data_row
    assert label.created_by() == label.client.get_user()

    label.delete()

    # TODO: Added sleep to account for ES from catching up to deletion.
    # Need a better way to query labels in `project.labels()`, because currently,
    # it intermittently takes too long to sync, causing flaky SDK tests
    time.sleep(5)

    assert list(project.labels()) == []
    assert list(data_row.labels()) == []


def test_label_export(configured_project_with_label):
    project, _, _, label = configured_project_with_label
    label_id = label.uid
    # Wait for exporter to retrieve latest labels
    time.sleep(10)

    exported_labels_url = project.export_labels()
    assert exported_labels_url is not None
    exported_labels = requests.get(exported_labels_url)
    labels = [example['ID'] for example in exported_labels.json()]
    assert labels[0] == label_id
    #TODO: Add test for bulk export back.
    # The new exporter doesn't work with the create_label mutation


def test_export_v2(configured_project_with_label):
    project, _, _, label = configured_project_with_label
    label_id = label.uid
    # Wait for exporter to retrieve latest labels
    time.sleep(10)
    task_name = "test_label_export_v2"

    # TODO: Right now we don't have a way to test this
    include_performance_details = True
    task = project.export_v2(
        task_name,
        params={
            "include_performance_details": include_performance_details,
            "include_labels": True
        })
    assert task.name == task_name
    task.wait_till_done()
    assert task.status == "COMPLETE"

    def download_result(result_url):
        response = requests.get(result_url)
        response.raise_for_status()
        data = [json.loads(line) for line in response.text.splitlines()]
        return data

    task_results = download_result(task.result_url)

    for task_result in task_results:
        assert len(task_result['errors']) == 0
        task_project = task_result['projects'][project.uid]
        task_project_label_ids_set = set(
            map(lambda prediction: prediction['id'], task_project['labels']))
        assert label_id in task_project_label_ids_set

        # TODO: Add back in when we have a way to test this
        # if include_performance_details:
        #     assert 'include_performance_details' in task_result and task_result[
        #         'include_performance_details'] is not None
        # else:
        #     assert 'include_performance_details' not in task_result or task_result[
        #         'include_performance_details'] is None


# TODO: Skipping this test in staging due to label not updating
@pytest.mark.skipif(condition=os.environ['LABELBOX_TEST_ENVIRON'] == "onprem" or
                    os.environ['LABELBOX_TEST_ENVIRON'] == "staging" or
                    os.environ['LABELBOX_TEST_ENVIRON'] == "local" or
                    os.environ['LABELBOX_TEST_ENVIRON'] == "custom",
                    reason="does not work for onprem")
def test_label_update(configured_project_with_label):
    _, _, _, label = configured_project_with_label
    label.update(label="something else")
    assert label.label == "something else"


def test_label_filter_order(configured_project_with_label):
    project, _, _, label = configured_project_with_label

    l1 = label
    project.create_label()
    l2 = next(project.labels())

    assert set(project.labels()) == {l1, l2}

    assert list(project.labels(order_by=Label.created_at.asc)) == [l1, l2]
    assert list(project.labels(order_by=Label.created_at.desc)) == [l2, l1]


def test_label_bulk_deletion(configured_project_with_label):
    project, _, _, _ = configured_project_with_label

    for _ in range(2):
        #only run twice, already have one label in the fixture
        project.create_label()
    labels = project.labels()
    l1 = next(labels)
    l2 = next(labels)
    l3 = next(labels)

    assert set(project.labels()) == {l1, l2, l3}

    Label.bulk_delete([l1, l3])

    # TODO: the sdk client should really abstract all these timing issues away
    # but for now bulk deletes take enough time that this test is flaky
    # add sleep here to avoid that flake
    time.sleep(5)

    assert set(project.labels()) == {l2}
