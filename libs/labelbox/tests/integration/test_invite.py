import pytest
from faker import Faker
from labelbox.schema.media_type import MediaType
from labelbox import ProjectRole

faker = Faker()


@pytest.fixture
def dummy_email():
    """Generate a random dummy email for testing"""
    return f"none+{faker.uuid4()}@labelbox.com"


@pytest.fixture(scope="module")
def test_project(client):
    """Create a temporary project for testing"""
    project = client.create_project(
        name=f"test-project-{faker.uuid4()}", media_type=MediaType.Image
    )
    yield project

    # Occurs after the test is finished based on scope
    project.delete()


@pytest.fixture
def org_invite(client, dummy_email):
    """Create an organization-level invite"""
    role = client.get_roles()["LABELER"]
    organization = client.get_organization()
    invite = organization.invite_user(dummy_email, role)

    yield invite

    if invite.uid:
        invite.cancel()


@pytest.fixture
def project_invite(client, test_project, dummy_email):
    """Create a project-level invite"""
    roles = client.get_roles()
    project_role = ProjectRole(project=test_project, role=roles["LABELER"])
    organization = client.get_organization()

    invite = organization.invite_user(
        dummy_email, roles["NONE"], project_roles=[project_role]
    )

    yield invite

    # Cleanup: Use invite.cancel() instead of organization.cancel_invite()
    if invite.uid:
        invite.cancel()


def test_get_organization_invites(client, org_invite):
    """Test retrieving all organization invites"""

    organization = client.get_organization()
    invites = organization.get_invites()
    invite_list = [invite for invite in invites]
    assert len(invite_list) > 0

    # Verify our test invite is in the list
    invite_emails = [invite.email for invite in invite_list]
    assert org_invite.email in invite_emails


def test_get_project_invites(client, test_project, project_invite):
    """Test retrieving project-specific invites"""

    organization = client.get_organization()
    project_invites = organization.get_project_invites(test_project.uid)
    invite_list = [invite for invite in project_invites]
    assert len(invite_list) > 0

    # Verify our test invite is in the list
    invite_emails = [invite.email for invite in invite_list]
    assert project_invite.email in invite_emails

    # Verify project role assignment
    found_invite = next(
        invite for invite in invite_list if invite.email == project_invite.email
    )
    assert len(found_invite.project_roles) == 1
    assert found_invite.project_roles[0].project.uid == test_project.uid


def test_cancel_invite(client, dummy_email):
    """Test canceling an invite"""
    # Create a new invite
    role = client.get_roles()["LABELER"]
    organization = client.get_organization()
    organization.invite_user(dummy_email, role)

    # Find the actual invite by email
    invites = organization.get_invites()
    found_invite = next(
        (invite for invite in invites if invite.email == dummy_email), None
    )
    assert found_invite is not None, f"Invite for {dummy_email} not found"

    # Cancel the invite using the found invite object
    result = found_invite.cancel()
    assert result is True

    # Verify the invite is no longer in the organization's invites
    invites = organization.get_invites()
    invite_emails = [i.email for i in invites]
    assert dummy_email not in invite_emails


def test_cancel_project_invite(client, test_project, dummy_email):
    """Test canceling a project invite"""
    # Create a project invite
    roles = client.get_roles()
    project_role = ProjectRole(project=test_project, role=roles["LABELER"])
    organization = client.get_organization()

    organization.invite_user(
        dummy_email, roles["NONE"], project_roles=[project_role]
    )

    # Find the actual invite by email
    invites = organization.get_invites()
    found_invite = next(
        (invite for invite in invites if invite.email == dummy_email), None
    )
    assert found_invite is not None, f"Invite for {dummy_email} not found"

    # Cancel the invite using the found invite object
    result = found_invite.cancel()
    assert result is True

    # Verify the invite is no longer in the project's invites
    project_invites = organization.get_project_invites(test_project.uid)
    invite_emails = [i.email for i in project_invites]
    assert dummy_email not in invite_emails


def test_project_invite_after_project_deletion(client, dummy_email):
    """Test that project invites are properly filtered when a project is deleted"""
    # Create two test projects
    project1 = client.create_project(
        name=f"test-project1-{faker.uuid4()}", media_type=MediaType.Image
    )
    project2 = client.create_project(
        name=f"test-project2-{faker.uuid4()}", media_type=MediaType.Image
    )

    # Create project roles
    roles = client.get_roles()
    project_role1 = ProjectRole(project=project1, role=roles["LABELER"])
    project_role2 = ProjectRole(project=project2, role=roles["LABELER"])

    # Invite user to both projects
    organization = client.get_organization()
    organization.invite_user(
        dummy_email, roles["NONE"], project_roles=[project_role1, project_role2]
    )

    # Delete one project
    project1.delete()

    # Find the invite and verify project roles
    invites = organization.get_invites()
    found_invite = next(
        (invite for invite in invites if invite.email == dummy_email), None
    )
    assert found_invite is not None, f"Invite for {dummy_email} not found"

    # Verify only one project role remains
    assert (
        len(found_invite.project_roles) == 1
    ), "Expected only one project role"
    assert found_invite.project_roles[0].project.uid == project2.uid

    # Cleanup
    project2.delete()
    if found_invite.uid:
        found_invite.cancel()
