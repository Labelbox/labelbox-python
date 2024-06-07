import pytest
import faker
from labelbox import Client
from labelbox.schema.user_group import UserGroup, UserGroupColor, UserGroupUser, UserGroupProject

data = faker.Faker()


class TestUserGroup:

    def test_existing_user_groups(self, client):
        group_name = data.name()
        # Create a new user group
        user_group = UserGroup(client)
        user_group.name = group_name
        user_group.color = UserGroupColor.BLUE
        user_group.create()

        # Verify that the user group was created successfully
        user_group_equal = UserGroup(client, id=user_group.id)
        assert user_group.id == user_group_equal.id
        assert user_group.name == user_group_equal.name
        assert user_group.color == user_group_equal.color

        user_group.delete()

    def test_create_user_group(self, client):
        group_name = data.name()
        # Create a new user group
        user_group = UserGroup(client)
        user_group.name = group_name
        user_group.color = UserGroupColor.BLUE
        user_group.create()

        # Verify that the user group was created successfully
        assert user_group.id is not None
        assert user_group.name == group_name
        assert user_group.color == UserGroupColor.BLUE

        user_group.delete()

    def test_update_user_group(self, client):
        # Create a new user group
        group_name = data.name()
        user_group = UserGroup(client)
        user_group.name = group_name
        user_group.create()

        # Update the user group
        group_name = data.name()
        user_group.name = group_name
        user_group.color = UserGroupColor.PURPLE
        user_group.update()

        # Verify that the user group was updated successfully
        assert user_group.name == group_name
        assert user_group.color == UserGroupColor.PURPLE

        user_group.delete()

    def test_get_user_groups(self, client):
        # Get all user groups
        user_groups_old = list(UserGroup.get_user_groups(client))

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
    def test_update_user_group(self, client, project_pack):
        # Create a new user group
        user_group = UserGroup(client)
        user_group.name = data.name()
        user_group.create()

        users = list(client.get_users())
        projects = project_pack

        # Add the user to the group
        user_group.users.add(users[0])
        user_group.projects.add(projects[0])
        user_group.update()

        # Verify that the user is added to the group
        assert users[0] in user_group.users
        assert projects[0] in user_group.projects

        user_group.delete()


if __name__ == "__main__":
    import subprocess
    subprocess.call(["pytest", "-v", __file__])
