import pytest

from labelbox.client import Project, Dataset
from labelbox.exceptions import InvalidQueryError


def test_project_dataset(client, rand_gen):
    project = client.create_project(name=rand_gen(Project.name))
    dataset = client.create_dataset(name=rand_gen(Project.name))

    assert len(list(project.datasets())) == 0
    assert len(list(dataset.projects())) == 0

    project.datasets.connect(dataset)

    assert {ds.uid for ds in project.datasets()} == {dataset.uid}
    assert {pr.uid for pr in dataset.projects()} == {project.uid}

    project_2 = client.create_project(name=rand_gen(Project.name))

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


def test_relationship_in_creation(client, rand_gen):
    # First create dataset, then related project
    dataset = client.create_dataset(name=rand_gen(str))
    # TODO support dataset connecting during project creation
    with pytest.raises(InvalidQueryError):
        project = client.create_project(name=rand_gen(str), datasets=dataset)
    # assert list(dataset.projects) == [project]
    # assert list(project.datasets) == [dataset]

    dataset.delete()
    # project.delete()

    # FIrst create project, then related dataset
    project = client.create_project(name=rand_gen(str))
    dataset = client.create_dataset(name=rand_gen(str), projects=project)
    assert list(dataset.projects()) == [project]
    assert list(project.datasets()) == [dataset]
    dataset.delete()
    project.delete()
