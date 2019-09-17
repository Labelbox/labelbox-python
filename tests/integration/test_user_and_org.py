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

    # TODO make organization fetchable on ID
    with pytest.raises(InvalidQueryError):
        list(organization.users())
        list(organization.projects())


def test_user_and_org_projects(client, rand_gen):
    user = client.get_user()
    projects = set(user.projects())

    project = client.create_project(name=rand_gen(Project.name))
    assert project.created_by() == user
    assert set(user.projects()) == projects.union({project})

    project.delete()
