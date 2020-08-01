import time

import pytest
import requests

from labelbox import Label

IMG_URL = "https://picsum.photos/200/300"


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


@pytest.mark.skip
def test_label_export(label_pack):
    project, dataset, data_row, label = label_pack
    project.create_label(data_row=data_row, label="l2")

    exported_labels_url = project.export_labels(5)
    assert exported_labels_url is not None
    if exported_labels_url is not None:
        exported_labels = requests.get(exported_labels_url)
        # TODO check content
        assert False


def test_label_update(label_pack):
    project, dataset, data_row, label = label_pack

    label.update(label="something else")
    assert label.label == "something else"


def test_label_filter_order(client, rand_gen):
    project = client.create_project(name=rand_gen(str))
    dataset_1 = client.create_dataset(name=rand_gen(str), projects=project)
    dataset_2 = client.create_dataset(name=rand_gen(str), projects=project)
    data_row_1 = dataset_1.create_data_row(row_data=IMG_URL)
    data_row_2 = dataset_2.create_data_row(row_data=IMG_URL)

    l1 = project.create_label(data_row=data_row_1, label="l1")
    l2 = project.create_label(data_row=data_row_2, label="l2")

    # Labels are not visible in the project immediately.
    time.sleep(10)

    # Filtering supported on dataset
    assert set(project.labels()) == {l1, l2}
    assert set(project.labels(datasets=[])) == set()
    assert set(project.labels(datasets=[dataset_1])) == {l1}
    assert set(project.labels(datasets=[dataset_2])) == {l2}
    assert set(project.labels(datasets=[dataset_1, dataset_2])) == {l1, l2}

    assert list(project.labels(order_by=Label.label.asc)) == [l1, l2]
    assert list(project.labels(order_by=Label.label.desc)) == [l2, l1]

    dataset_1.delete()
    dataset_2.delete()
    project.delete()


def test_label_bulk_deletion(project, rand_gen):
    dataset = project.client.create_dataset(name=rand_gen(str),
                                            projects=project)
    row_1 = dataset.create_data_row(row_data=IMG_URL)
    row_2 = dataset.create_data_row(row_data=IMG_URL)

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
