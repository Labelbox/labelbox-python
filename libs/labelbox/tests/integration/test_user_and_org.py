from labelbox.schema.project import Project


def test_user(client):
    user = client.get_user()
    assert user.uid is not None
    assert user.organization() == client.get_organization()


def test_organization(client):
    organization = client.get_organization()
    assert organization.uid is not None
    assert client.get_user() in set(organization.users())


def test_user_and_org_projects(client, project):
    user = client.get_user()
    org = client.get_organization()
    user_project = user.projects(where=Project.uid == project.uid)
    org_project = org.projects(where=Project.uid == project.uid)

    assert user_project
    assert org_project
