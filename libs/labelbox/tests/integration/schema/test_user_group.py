import pytest
import faker
from labelbox import Client
from labelbox.schema.user_group import UserGroup, UserGroupColor, UserGroupUser, UserGroupProject

data = faker.Faker()

@pytest.fixture
def user_group(client):
    group_name = data.name()
    # Create a new user group
    user_group = UserGroup(client)
    user_group.name = group_name
    user_group.color = UserGroupColor.BLUE
    user_group.create()

    yield user_group

    user_group.delete()


def test_existing_user_groups(user_group, client):
    # Verify that the user group was created successfully
    user_group_equal = UserGroup(client)
    user_group_equal.id = user_group.id
    user_group_equal.get()
    assert user_group.id == user_group_equal.id
    assert user_group.name == user_group_equal.name
    assert user_group.color == user_group_equal.color


def test_create_user_group(user_group):
    # Verify that the user group was created successfully
    assert user_group.id is not None
    assert user_group.name is not None
    assert user_group.color == UserGroupColor.BLUE


def test_update_user_group(user_group):
    # Update the user group
    group_name = data.name()
    user_group.name = group_name
    user_group.color = UserGroupColor.PURPLE
    user_group.update()

    # Verify that the user group was updated successfully
    assert user_group.name == group_name
    assert user_group.color == UserGroupColor.PURPLE


def test_get_user_groups(user_group, client):
    # Get all user groups
    user_groups_old = list(UserGroup.get_user_groups(client))

    # manual delete for iterators
    group_name = data.name()
    user_group = UserGroup(client)
    user_group.name = group_name
    user_group.create()

    user_groups_new = list(UserGroup.get_user_groups(client))

    # Verify that at least one user group is returned
    assert len(user_groups_new) > 0
    assert len(user_groups_new) == len(user_groups_old) + 1

    # Verify that each user group has a valid ID and name
    for user_group in user_groups_new:
        assert user_group.id is not None
        assert user_group.name is not None

    user_group.delete()


# project_pack creates two projects
def test_update_user_group(user_group, client, project_pack):
    users = list(client.get_users())
    projects = project_pack

    # Add the user to the group
    user = users[0]
    user = UserGroupUser(
        id=user.uid,
        email=user.email
    )
    project = projects[0]
    project = UserGroupProject(
        id=project.uid,
        name=project.name
    )
    user_group.users.add(user)
    user_group.projects.add(project)
    user_group.update()

    # Verify that the user is added to the group
    assert user in user_group.users
    assert project in user_group.projects


if __name__ == "__main__":
    import subprocess
    subprocess.call(["pytest", "-v", __file__])