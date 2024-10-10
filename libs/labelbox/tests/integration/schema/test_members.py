from uuid import uuid4

import faker
from labelbox.schema.member import Member, ProjectMembership
import pytest

from labelbox.exceptions import (
    ResourceNotFoundError,
)
from labelbox.schema.user_group import UserGroup, UserGroupColor

data = faker.Faker()


@pytest.fixture
def current_member(client):
    yield Member(client=client).get()


@pytest.fixture
def member(client, current_member):
    members = list(Member(client).get_members())
    test_member = None
    for member in members:
        if member.id != current_member.id:
            test_member = member
    return test_member


@pytest.fixture
def user_group(client):
    group_name = data.name()
    user_group = UserGroup(client)
    user_group.name = group_name
    user_group.color = UserGroupColor.BLUE

    yield user_group.create()

    user_group.delete()


def test_get_member(current_member, client):
    current_member_eq = Member(client)
    current_member_eq.get()
    assert current_member_eq.id == current_member.id
    assert current_member_eq.email == current_member.email


def test_throw_error_cannot_get_user_group_with_invalid_id(client):
    Member = UserGroup(Member=client, id=str(uuid4()))
    with pytest.raises(ResourceNotFoundError):
        Member.get()


def test_throw_error_when_deleting_self(current_member, client):
    with pytest.raises(ValueError):
        current_member.delete()


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

    # Verify that the member was updated successfully
    assert test_member.email == updated_member.email
    for project in project_pack:
        assert (
            ProjectMembership(project_id=project.uid, role=labeler_role)
            in updated_member.project_memberships
        )
    assert user_group.id in updated_member.user_group_ids
    assert updated_member.default_role == reviewer_role

    # Remove memberships and check if updated
    updated_member.project_memberships = set()
    updated_member.user_group_ids = set()
    updated_member.default_role = labeler_role
    updated_member.can_access_all_projects = True
    updated_member = updated_member.update()

    assert updated_member.project_memberships == set()
    assert updated_member.user_group_ids == set()
    assert updated_member.default_role == labeler_role
    assert updated_member.can_access_all_projects


def test_get_members(test_member, current_member, client):
    members = list(Member(client).get_members(search=current_member.email))
    assert current_member in members
    members = list(
        Member(client).get_members(roles=[current_member.default_role])
    )
    assert current_member in members
    members = list(Member(client).get_members())
    assert test_member in members
    assert current_member in members


if __name__ == "__main__":
    import subprocess

    subprocess.call(["pytest", "-v", __file__])
