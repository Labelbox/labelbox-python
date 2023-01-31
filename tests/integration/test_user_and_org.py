def test_user(client):
    user = client.get_user()
    assert user.uid is not None
    assert user.organization() == client.get_organization()


def test_organization(client):
    organization = client.get_organization()
    assert organization.uid is not None
    assert client.get_user() in set(organization.users())


def test_user_and_org_projects(project):
    client = project.client
    user = client.get_user()
    org = client.get_organization()
    user_projects = set(user.projects())
    org_projects = set(org.projects())

    assert project.created_by() == user
    assert project.organization() == org
    assert project in user_projects
    assert project in org_projects