import time

import pytest
import requests

from labelbox import Label


def test_labels(configured_project_with_label):
    project, _, data_row, label = configured_project_with_label

    assert list(project.labels()) == [label]
    assert list(data_row.labels()) == [label]

    assert label.project() == project
    assert label.data_row() == data_row
    assert label.created_by() == label.client.get_user()

    label.delete()

    assert list(project.labels()) == []
    assert list(data_row.labels()) == []


def test_label_export(configured_project_with_label):
    project, _, _, label = configured_project_with_label
    label_id = label.uid

    exported_labels_url = project.export_labels()
    assert exported_labels_url is not None
    exported_labels = requests.get(exported_labels_url)
    labels = [example['ID'] for example in exported_labels.json()]
    assert labels[0] == label_id
    # TODO: Add test for bulk export back.
    # The new exporter doesn't work with the create_label mutation


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
