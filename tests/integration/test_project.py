import pytest

from labelbox import Project
from labelbox.exceptions import InvalidQueryError


def test_project(client, rand_gen):
    before = list(client.get_projects())
    for o in before:
        assert isinstance(o, Project)

    data = {"name": rand_gen(str), "description": rand_gen(str)}
    project = client.create_project(**data)
    assert project.name == data["name"]
    assert project.description == data["description"]

    after = list(client.get_projects())
    assert len(after) == len(before) + 1
    assert project in after

    project = client.get_project(project.uid)
    assert project.name == data["name"]
    assert project.description == data["description"]

    update_data = {"name": rand_gen(str), "description": rand_gen(str)}
    project.update(**update_data)
    # Test local object updates.
    assert project.name == update_data["name"]
    assert project.description == update_data["description"]

    # Test remote updates.
    project = client.get_project(project.uid)
    assert project.name == update_data["name"]
    assert project.description == update_data["description"]

    project.delete()
    final = list(client.get_projects())
    assert project not in final
    assert set(final) == set(before)

    # TODO this should raise ResourceNotFoundError, but it doesn't
    project = client.get_project(project.uid)


def test_project_filtering(client, rand_gen):
    name_1 = rand_gen(str)
    name_2 = rand_gen(str)
    p1 = client.create_project(name=name_1)
    p2 = client.create_project(name=name_2)

    assert list(client.get_projects(where=Project.name==name_1)) == [p1]
    assert list(client.get_projects(where=Project.name==name_2)) == [p2]

    p1.delete()
    p2.delete()


def test_upsert_review_queue(project):
    project.upsert_review_queue(0.6)


def test_extend_reservations(project):
    assert project.extend_reservations("LabelingQueue") == 0
    assert project.extend_reservations("ReviewQueue") == 0
    with pytest.raises(InvalidQueryError):
        project.extend_reservations("InvalidQueueType")


def test_project_bulk_delete_labels(label_pack):
    project, _, data_row, label = label_pack

    import time
    time.sleep(7)

    assert set(project.labels()) == {label}
    assert project.bulk_delete_labels() == 1
    assert set(project.labels()) == set()

    l1 = project.create_label(data_row=data_row, label="label")
    l2 = project.create_label(data_row=data_row, label="babel")
    l3 = project.create_label(data_row=data_row, label="bambi")
    l4 = project.create_label(data_row=data_row, label="label")
    l5 = project.create_label(data_row=data_row, label="godel")

    time.sleep(8)
    assert set(project.labels()) == {l1, l2, l3, l4, l5}

    assert project.bulk_delete_labels(labels=[l4, l5]) == 2
    time.sleep(8)
    assert set(project.labels()) == {l1, l2, l3}

    assert project.bulk_delete_labels(label_contains="drift") == 0
    # TODO The test below fail due the `label_contains` filter not
    # working as expected.
    # assert project.bulk_delete_labels(label_contains="ba") == 2
    # time.sleep(8)
    # assert set(project.labels()) == {l1, l3, l4, l5}

    # assert project.bulk_delete_labels(labels=data_row.labels()) == 2
    assert project.bulk_delete_labels(labels=data_row.labels()) == 3
    time.sleep(8)
    assert set(project.labels()) == set()
