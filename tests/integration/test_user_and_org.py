import pytest

from labelbox import Project, Dataset, DataRow
from labelbox.exceptions import NetworkError, InvalidQueryError


def test_user(client):
    user = client.get_user()
    assert user.uid is not None
    assert user.organization() == client.get_organization()


def test_organization(client):
    organization = client.get_organization()
    assert organization.uid is not None
    assert client.get_user() in set(organization.users())


def test_user_and_org_projects(client, rand_gen):
    user = client.get_user()
    org = client.get_organization()
    user_projects = set(user.projects())
    org_projects = set(org.projects())

    project = client.create_project(name=rand_gen(Project.name))
    assert project.created_by() == user
    assert project.organization() == org
    assert set(user.projects()) == user_projects.union({project})
    assert set(org.projects()) == org_projects.union({project})

    project.delete()
