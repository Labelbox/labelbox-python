import time

import pytest
import requests

from labelbox import Label
from labelbox.exceptions import InvalidQueryError


IMG_URL = "https://picsum.photos/200/300"


def test_labels(client, rand_gen):
    project = client.create_project(name=rand_gen(str))
    dataset = client.create_dataset(name=rand_gen(str), projects=project)

    data_row = dataset.create_data_row(row_data=IMG_URL)

    label = project.create_label(data_row=data_row, label="test",
                                 seconds_to_label=0.0)

    # Labels are not visible in the project immediately.
    time.sleep(10)

    assert list(project.labels()) == [label]
    assert list(data_row.labels()) == [label]

    assert label.project() == project
    assert label.data_row() == data_row

    # TODO ensure that a label can be deleted
    with pytest.raises(InvalidQueryError):
        label.delete()

    dataset.delete()
    project.delete()


def test_label_export(client, rand_gen):
    # TODO test
    return
    project = client.create_project(name=rand_gen(str))
    dataset = client.create_dataset(name=rand_gen(str), projects=project)
    data_row = dataset.create_data_row(row_data=IMG_URL)
    project.create_label(data_row=data_row, label="l1", seconds_to_label=0.2)
    project.create_label(data_row=data_row, label="l2", seconds_to_label=0.3)

    exported_labels_url = project.export_labels()
    assert exported_labels_url is not None
    if exported_labels_url is not None:
        exported_labels = requests.get(exported_labels_url)
        # TODO check content

    dataset.delete()
    project.delete()


def test_label_update(client, rand_gen):
    project = client.create_project(name=rand_gen(str))
    dataset = client.create_dataset(name=rand_gen(str), projects=project)
    data_row = dataset.create_data_row(row_data=IMG_URL)

    label = project.create_label(data_row=data_row, label="l1", seconds_to_label=0.0)

    assert label.label == "l1"
    label.update(label="something else")
    assert label.label == "something else"

    # Check the label got updated server-side
    # Labels are not visible in the project immediately.
    time.sleep(10)
    assert list(project.labels())[0].label == "something else"

    dataset.delete()
    project.delete()


def test_label_filter_order(client, rand_gen):
    project = client.create_project(name=rand_gen(str))
    dataset = client.create_dataset(name=rand_gen(str), projects=project)
    data_row = dataset.create_data_row(row_data=IMG_URL)

    l1 = project.create_label(data_row=data_row, label="l1", seconds_to_label=0.3)
    l2 = project.create_label(data_row=data_row, label="l2", seconds_to_label=0.1)

    # Labels are not visible in the project immediately.
    time.sleep(10)

    # Filtering is not supported
    with pytest.raises(InvalidQueryError) as exc_info:
        project.labels(where=Label.label=="l1")
    assert exc_info.value.message == \
        "Relationship Project.labels doesn't support filtering"

    assert list(project.labels(order_by=Label.label.asc)) == [l1, l2]
    assert list(project.labels(order_by=Label.label.desc)) == [l2, l1]
    assert list(project.labels(order_by=Label.seconds_to_label.asc)) == [l2, l1]
    assert list(project.labels(order_by=Label.seconds_to_label.desc)) == [l1, l2]

    dataset.delete()
    project.delete()
