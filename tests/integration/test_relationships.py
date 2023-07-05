import pytest

from labelbox.exceptions import InvalidQueryError
from labelbox.schema.queue_mode import QueueMode


def test_project_dataset(client, rand_gen):
    project = client.create_project(name=rand_gen(str),
                                    queue_mode=QueueMode.Batch)
    dataset = client.create_dataset(name=rand_gen(str))

    assert len(list(project.datasets())) == 0
    assert len(list(dataset.projects())) == 0

    dataset.create_data_row(row_data="test")

    project.datasets.connect(dataset)

    assert {ds.uid for ds in project.datasets()} == {dataset.uid}
    assert {pr.uid for pr in dataset.projects()} == {project.uid}

    project_2 = client.create_project(name=rand_gen(str),
                                      queue_mode=QueueMode.Batch)

    # Currently it's not possible to connect a project and dataset
    # by updating dataset.
    # TODO make this possible
    with pytest.raises(InvalidQueryError):
        dataset.projects.connect(project_2)
    project_2.datasets.connect(dataset)

    assert {ds.uid for ds in project.datasets()} == {dataset.uid}
    assert {ds.uid for ds in project_2.datasets()} == {dataset.uid}
    assert {pr.uid for pr in dataset.projects()} == {project.uid, project_2.uid}

    project.datasets.disconnect(dataset)
    assert {ds.uid for ds in project.datasets()} == set()
    assert {ds.uid for ds in project_2.datasets()} == {dataset.uid}
    assert {pr.uid for pr in dataset.projects()} == {project_2.uid}

    dataset.delete()
    assert {ds.uid for ds in project.datasets()} == set()
    assert {ds.uid for ds in project_2.datasets()} == set()

    project.delete()
    project_2.delete()
