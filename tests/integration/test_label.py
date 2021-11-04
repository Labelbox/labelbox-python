from labelbox.schema.labeling_frontend import LabelingFrontend
import time
import json

import pytest
import requests

from labelbox import Label


def test_labels(label_pack):
    project, dataset, data_row, label = label_pack

    # Labels are not visible in the project immediately.
    time.sleep(10)

    assert list(project.labels()) == [label]
    assert list(data_row.labels()) == [label]

    assert label.project() == project
    assert label.data_row() == data_row
    assert label.created_by() == label.client.get_user()

    label.delete()

    # Labels are not visible in the project immediately.
    time.sleep(10)

    assert list(project.labels()) == []
    assert list(data_row.labels()) == []


def test_label_export(client, configured_project_with_label):
    project, label_id = configured_project_with_label

    exported_labels_url = project.export_labels()
    assert exported_labels_url is not None
    exported_labels = requests.get(exported_labels_url)
    labels = [example['ID'] for example in exported_labels.json()]
    assert labels[0] == label_id
    # TODO: Add test for bulk export back.
    # The new exporter doesn't work with the create_label mutation


def test_label_update(label_pack):
    project, dataset, data_row, label = label_pack
    label.update(label="something else")
    assert label.label == "something else"


def test_label_filter_order(client, project, rand_gen, image_url):
    dataset_1 = client.create_dataset(name=rand_gen(str), projects=project)
    dataset_2 = client.create_dataset(name=rand_gen(str), projects=project)
    data_row_1 = dataset_1.create_data_row(row_data=image_url)
    data_row_2 = dataset_2.create_data_row(row_data=image_url)

    l1 = project.create_label(data_row=data_row_1, label="l1")
    time.sleep(1)  #Ensure there is no race condition
    l2 = project.create_label(data_row=data_row_2, label="l2")

    # Labels are not visible in the project immediately.
    time.sleep(20)

    # Filtering supported on dataset
    assert set(project.labels()) == {l1, l2}
    assert set(project.labels(datasets=[])) == set()
    assert set(project.labels(datasets=[dataset_1])) == {l1}
    assert set(project.labels(datasets=[dataset_2])) == {l2}
    assert set(project.labels(datasets=[dataset_1, dataset_2])) == {l1, l2}

    assert list(project.labels(order_by=Label.created_at.asc)) == [l1, l2]
    assert list(project.labels(order_by=Label.created_at.desc)) == [l2, l1]

    dataset_1.delete()
    dataset_2.delete()
    project.delete()


def test_label_bulk_deletion(project, rand_gen, image_url):
    dataset = project.client.create_dataset(name=rand_gen(str),
                                            projects=project)
    row_1 = dataset.create_data_row(row_data=image_url)
    row_2 = dataset.create_data_row(row_data=image_url)

    l1 = project.create_label(data_row=row_1, label="l1")
    l2 = project.create_label(data_row=row_1, label="l2")
    l3 = project.create_label(data_row=row_2, label="l3")

    # Labels are not visible in the project immediately.
    time.sleep(10)

    assert set(project.labels()) == {l1, l2, l3}

    Label.bulk_delete([l1, l3])

    # TODO: the sdk client should really abstract all these timing issues away
    # but for now bulk deletes take enough time that this test is flaky
    # add sleep here to avoid that flake
    time.sleep(5)

    assert set(project.labels()) == {l2}

    dataset.delete()
