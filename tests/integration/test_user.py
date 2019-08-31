import pytest

from labelbox import Project, Dataset, DataRow
from labelbox.exceptions import NetworkError


def test_user(client):
    user = client.get_user()
    assert user.uid is not None


def test_user_projects(client, rand_gen):
    user = client.get_user()
    projects = list(user.projects())

    project = client.create_project(name=rand_gen(Project.name))
    assert len(list(user.projects())) == len(projects) + 1

    project.delete()
