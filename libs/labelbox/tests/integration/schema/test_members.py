import faker
from labelbox.schema.member import Member, ProjectMembership
import pytest
from labelbox.exceptions import (
    ResourceNotFoundError,
)
from labelbox.schema.user_group import UserGroup, UserGroupColor

from libs.labelbox.tests.conftest import AdminClient, Environ
import os

data = faker.Faker()


@pytest.fixture(scope="session")
def current_member(client):
    current_member = Member(client=client).get()
    yield current_member


@pytest.fixture(scope="session")
def user_group(client):
    group_name = data.name()
    user_group = UserGroup(client=client)
    user_group.name = group_name
    user_group.color = UserGroupColor.BLUE

    yield user_group.create()

    user_group.delete()


@pytest.fixture(scope="module")
def test_member(client, current_member, admin_client: AdminClient):
    admin_client = admin_client(Environ.STAGING)
    admin_client._create_user(client.get_organization().uid)
    members = list(Member(client=client).get_members(search="email@email.com"))
    test_member = None
    for member in members:
        if member.id != current_member.id:
            test_member = member
    if test_member is None:
        raise ValueError("Valid member was not found")
    yield test_member
    # delete member for clean up
    test_member.delete()


def test_get_member(current_member, client):
    current_member_eq = Member(client=client).get()
    assert current_member_eq.id == current_member.id
    assert current_member_eq.email == current_member.email


def test_throw_error_when_deleting_self(current_member):
    with pytest.raises(ValueError):
        current_member.delete()


@pytest.mark.skipif(
    condition=os.environ["LABELBOX_TEST_ENVIRON"] != "staging",
    reason="admin client only works in staging",
)
def test_update_member(client, test_member, project_pack, user_group):
    labeler_role = client.get_roles()["LABELER"]
    reviewer_role = client.get_roles()["REVIEWER"]
    for project in project_pack:
        test_member.project_memberships.add(
            ProjectMembership(project_id=project.uid, role=labeler_role)
        )
    test_member.default_role = reviewer_role
    test_member.user_group_ids.add(user_group.id)
    test_member.can_access_all_projects = False
    updated_member = test_member.update()
    updated_member = updated_member.get()

    # Verify that the member was updated successfully
    assert test_member.email == updated_member.email
    for project in project_pack:
        assert (
            ProjectMembership(project_id=project.uid, role=labeler_role)
            in updated_member.project_memberships
        )
    assert user_group.id in updated_member.user_group_ids
    assert updated_member.default_role == reviewer_role

    # update project role for one of the projects
    project = project_pack[0]
    project_membership = ProjectMembership(
        project_id=project.uid, role=reviewer_role
    )
    updated_member.project_memberships.add(project_membership)
    updated_member = updated_member.update()
    assert project_membership in updated_member.get().project_memberships

    # Remove memberships and check if updated
    updated_member.project_memberships = set()
    updated_member.user_group_ids = set()
    updated_member.default_role = labeler_role
    updated_member.can_access_all_projects = True
    updated_member = updated_member.update()
    updated_member = updated_member.get()

    assert updated_member.project_memberships == set()
    assert updated_member.user_group_ids == set()
    assert updated_member.default_role == labeler_role
    assert updated_member.can_access_all_projects


@pytest.mark.skipif(
    condition=os.environ["LABELBOX_TEST_ENVIRON"] != "staging",
    reason="admin client only works in staging",
)
def test_get_members(test_member, current_member, client):
    member_ids = [
        member.id
        for member in Member(client=client).get_members(
            search=test_member.email
        )
    ]
    assert test_member.id in member_ids

    # TODO<Gabefire>: can not search for roles or groups as it is too flaky will need to add in once user groups are harden

    member_ids = [member.id for member in Member(client=client).get_members()]
    assert test_member.id in member_ids
    assert current_member.id in member_ids


@pytest.mark.skipif(
    condition=os.environ["LABELBOX_TEST_ENVIRON"] != "staging",
    reason="admin client only works in staging",
)
def test_delete_member(test_member, current_member):
    email = test_member.email
    id = test_member.id
    test_member.delete()
    member_ids = [
        member.id for member in current_member.get_members(search=email)
    ]
    assert id not in member_ids


if __name__ == "__main__":
    import subprocess

    subprocess.call(["pytest", "-v", __file__])
