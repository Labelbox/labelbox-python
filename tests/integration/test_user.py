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
    # TODO ensure that the user can be reached from the Project side
    # this can be done by changing the relationship query not to include
    # a "where" clause when not necessary, or by making the server-side
    # consistent w.r.t. accepting "where" clauses
    with pytest.raises(NetworkError):
        project_creator = project.created_by()

    assert len(list(user.projects())) == len(projects) + 1

    project.delete()
