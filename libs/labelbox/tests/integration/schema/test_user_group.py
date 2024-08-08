import pytest
import faker
from uuid import uuid4
from labelbox import Client
from labelbox.schema.user_group import UserGroup, UserGroupColor
from labelbox.exceptions import ResourceNotFoundError, ResourceCreationError, UnprocessableEntityError

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


def test_get_user_group(user_group, client):
    # Verify that the user group was created successfully
    user_group_equal = UserGroup(client)
    user_group_equal.id = user_group.id
    user_group_equal.get()
    assert user_group.id == user_group_equal.id
    assert user_group.name == user_group_equal.name
    assert user_group.color == user_group_equal.color


def test_throw_error_get_user_group_no_id(user_group, client):
    old_id = user_group.id
    with pytest.raises(ValueError):
        user_group.id = ""
        user_group.get()
    user_group.id = old_id


def test_throw_error_cannot_get_user_group_with_invalid_id(client):
    user_group = UserGroup(client=client, id=str(uuid4()))
    with pytest.raises(ResourceNotFoundError):
        user_group.get()


def test_throw_error_when_retrieving_deleted_group(client):
    user_group = UserGroup(client=client, name=data.name())
    user_group.create()

    assert user_group.get() is not None
    user_group.delete()

    with pytest.raises(ResourceNotFoundError):
        user_group.get()


def test_create_user_group_no_name(client):
    # Create a new user group
    with pytest.raises(ResourceCreationError):
        user_group = UserGroup(client)
        user_group.name = "   "
        user_group.color = UserGroupColor.BLUE
        user_group.create()


def test_cannot_create_group_with_same_name(client, user_group):
    with pytest.raises(ResourceCreationError):
        user_group_2 = UserGroup(client=client, name=user_group.name)
        user_group_2.create()


def test_create_user_group(user_group):
    # Verify that the user group was created successfully
    assert user_group.id is not None
    assert user_group.name is not None
    assert user_group.color == UserGroupColor.BLUE


def test_create_user_group_advanced(client, project_pack):
    group_name = data.name()
    # Create a new user group
    user_group = UserGroup(client)
    user_group.name = group_name
    user_group.color = UserGroupColor.BLUE
    users = list(client.get_users())
    projects = project_pack
    user = users[0]
    project = projects[0]
    user_group.users.add(user)
    user_group.projects.add(project)

    user_group.create()

    assert user_group.id is not None
    assert user_group.name is not None
    assert user_group.color == UserGroupColor.BLUE
    assert project in user_group.projects
    assert user in user_group.users

    user_group.delete()


def test_update_user_group(user_group):
    # Update the user group
    group_name = data.name()
    user_group.name = group_name
    user_group.color = UserGroupColor.PURPLE
    updated_user_group = user_group.update()

    # Verify that the user group was updated successfully
    assert user_group.name == updated_user_group.name
    assert user_group.name == group_name
    assert user_group.color == updated_user_group.color
    assert user_group.color == UserGroupColor.PURPLE


def test_throw_error_cannot_update_name_to_empty_string(user_group):
    with pytest.raises(ValueError):
        user_group.name = ""
        user_group.update()


def test_throw_error_cannot_update_id_to_empty_string(user_group):
    old_id = user_group.id
    with pytest.raises(ValueError):
        user_group.id = ""
        user_group.update()
    user_group.id = old_id


def test_cannot_update_group_id(user_group):
    old_id = user_group.id
    with pytest.raises(ResourceNotFoundError):
        user_group.id = str(uuid4())
        user_group.update()
    # prevent leak
    user_group.id = old_id


def test_get_user_groups_with_creation_deletion(client):
    user_group = None
    try: 
        # Get all user groups
        user_groups = list(UserGroup(client).get_user_groups())

        # manual delete for iterators
        group_name = data.name()
        user_group = UserGroup(client)
        user_group.name = group_name
        user_group.create()

        user_groups_post_creation = list(UserGroup(client).get_user_groups())

        # Verify that at least one user group is returned
        assert len(user_groups_post_creation) > 0
        assert len(user_groups_post_creation) == len(user_groups) + 1

        # Verify that each user group has a valid ID and name
        for ug in user_groups_post_creation:
            assert ug.id is not None
            assert ug.name is not None

        user_group.delete()
        user_group = None

        user_groups_post_deletion = list(UserGroup(client).get_user_groups())

        assert len(user_groups_post_deletion) == len(user_groups_post_creation) - 1

    finally:
        if user_group:
            user_group.delete()


# project_pack creates two projects
def test_update_user_group_users_projects(user_group, client, project_pack):
    users = list(client.get_users())
    projects = project_pack

    # Add the user to the group
    user = users[0]
    project = projects[0]
    user_group.users.add(user)
    user_group.projects.add(project)
    user_group.update()

    # Verify that the user is added to the group
    assert user in user_group.users
    assert project in user_group.projects


def test_delete_user_group_with_same_id(client):
    user_group_1 = UserGroup(client, name=data.name())
    user_group_1.create()
    user_group_1.delete()
    user_group_2 = UserGroup(client=client, id=user_group_1.id)

    with pytest.raises(ResourceNotFoundError):
        user_group_2.delete()


def test_throw_error_when_deleting_invalid_id_group(client):
    with pytest.raises(ResourceNotFoundError):
        user_group = UserGroup(client=client, id=str(uuid4()))
        user_group.delete()


def test_throw_error_delete_user_group_no_id(user_group, client):
    old_id = user_group.id
    with pytest.raises(ValueError):
        user_group.id = ""
        user_group.delete()
    user_group.id = old_id


if __name__ == "__main__":
    import subprocess
    subprocess.call(["pytest", "-v", __file__])