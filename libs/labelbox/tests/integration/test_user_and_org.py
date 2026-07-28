from labelbox.schema.project import Project


def test_user(client):
    user = client.get_user()
    assert user.uid is not None
    assert user.organization() == client.get_organization()
    assert hasattr(user, "last_login_at")
    # Nullable: None until the user has logged in after tracking was enabled.
    assert user.last_login_at is None or hasattr(user.last_login_at, "year")


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
