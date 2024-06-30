import pytest
from unittest.mock import MagicMock
from labelbox import Client
from labelbox.exceptions import ResourceCreationError
from labelbox.schema.user import User
from labelbox.schema.user_group import UserGroup, UserGroupColor, UserGroupUser, UserGroupProject


class TestUserGroupColor:

    def test_user_group_color_values(self):
        assert UserGroupColor.BLUE.value == "9EC5FF"
        assert UserGroupColor.PURPLE.value == "CEB8FF"
        assert UserGroupColor.ORANGE.value == "FFB35F"
        assert UserGroupColor.CYAN.value == "4ED2F9"
        assert UserGroupColor.PINK.value == "FFAEA9"
        assert UserGroupColor.LIGHT_PINK.value == "FFA9D5"
        assert UserGroupColor.GREEN.value == "3FDC9A"
        assert UserGroupColor.YELLOW.value == "E7BF00"
        assert UserGroupColor.GRAY.value == "B8C4D3"


class TestUserGroupUser:

    def test_user_group_user_attributes(self):
        user = UserGroupUser(id="user_id", email="test@example.com")
        assert user.id == "user_id"
        assert user.email == "test@example.com"

    def test_user_group_user_equality(self):
        user1 = UserGroupUser(id="user_id", email="test@example.com")
        user2 = UserGroupUser(id="user_id", email="test@example.com")
        assert user1 == user2

    def test_user_group_user_hash(self):
        user = UserGroupUser(id="user_id", email="test@example.com")
        assert hash(user) == hash("user_id")


class TestUserGroupProject:

    def test_user_group_project_attributes(self):
        project = UserGroupProject(id="project_id", name="Test Project")
        assert project.id == "project_id"
        assert project.name == "Test Project"

    def test_user_group_project_equality(self):
        project1 = UserGroupProject(id="project_id", name="Test Project")
        project2 = UserGroupProject(id="project_id", name="Test Project")
        assert project1 == project2

    def test_user_group_project_hash(self):
        project = UserGroupProject(id="project_id", name="Test Project")
        assert hash(project) == hash("project_id")


class TestUserGroup:

    def setup_method(self):
        self.client = MagicMock(Client)
        self.client.enable_experimental = True
        self.group = UserGroup(client=self.client)
  
    def test_constructor_experimental_needed(self):
        client = MagicMock(Client)
        client.enable_experimental = False
        with pytest.raises(RuntimeError):
            group = UserGroup(client)

    def test_constructor(self):
        group = UserGroup(self.client)

        assert group.id == ""
        assert group.name == ""
        assert group.color is UserGroupColor.BLUE
        assert len(group.projects) == 0
        assert len(group.users) == 0

    def test_get(self):
        projects = [
            {
                "id": "project_id_1",
                "name": "project_1"
            },
            {
                "id": "project_id_2",
                "name": "project_2"
            }
        ]
        group_members = [
            {
                "id": "user_id_1",
                "email": "email_1"
            },
            {
                "id": "user_id_2",
                "email": "email_2"
            }
        ]
        self.client.execute.return_value = {
            "userGroup": {
                "id": "group_id",
                "name": "Test Group",
                "color": "4ED2F9",
                "projects": {
                    "nodes": projects
                },
                "members": {
                    "nodes": group_members
                }
            }
        }
        group = UserGroup(self.client)
        assert group.id == ""
        assert group.name == ""
        assert group.color is UserGroupColor.BLUE
        assert len(group.projects) == 0
        assert len(group.users) == 0

        group.id = "group_id"
        group.get()

        assert group.id == "group_id"
        assert group.name == "Test Group"
        assert group.color is UserGroupColor.CYAN
        assert len(group.projects) == 2
        assert len(group.users) == 2

    def test_id(self):
        group = self.group
        assert group.id == ""

    def test_name(self):
        group = self.group
        assert group.name == ""

        group.name = "New Group"
        assert group.name == "New Group"

        group.name = "Another Group"
        assert group.name == "Another Group"

    def test_color(self):
        group = self.group
        assert group.color is UserGroupColor.BLUE

        group.color = UserGroupColor.PINK
        assert group.color == UserGroupColor.PINK

        group.color = UserGroupColor.YELLOW
        assert group.color == UserGroupColor.YELLOW

    def test_users(self):
        group = self.group
        assert len(group.users) == 0

        group.users = {UserGroupUser(id="user_id", email="user_id@email")}
        assert len(group.users) == 1

        group.users = {
            UserGroupUser(id="user_id", email="user_id@email"),
            UserGroupUser(id="user_id", email="user_id@email")
        }
        assert len(group.users) == 1

        group.users = {}
        assert len(group.users) == 0

    def test_projects(self):
        group = self.group
        assert len(group.projects) == 0

        group.projects = {
            UserGroupProject(id="project_id", name="Test Project")
        }
        assert len(group.projects) == 1

        group.projects = {
            UserGroupProject(id="project_id", name="Test Project"),
            UserGroupProject(id="project_id", name="Test Project")
        }
        assert len(group.projects) == 1

        group.projects = {}
        assert len(group.projects) == 0

    def test_update(self):
        group = self.group
        group.id = "group_id"
        group.name = "Test Group"
        group.color = UserGroupColor.BLUE
        group.users = {UserGroupUser(id="user_id", email="test@example.com")}
        group.projects = {
            UserGroupProject(id="project_id", name="Test Project")
        }

        updated_group = group.update()

        execute = self.client.execute.call_args[0]

        assert "UpdateUserGroupPyApi" in execute[0]
        assert execute[1]["id"] == "group_id"
        assert execute[1]["name"] == "Test Group"
        assert execute[1]["color"] == UserGroupColor.BLUE.value
        assert len(execute[1]["userIds"]) == 1
        assert list(execute[1]["userIds"])[0] == "user_id"
        assert len(execute[1]["projectIds"]) == 1
        assert list(execute[1]["projectIds"])[0] == "project_id"

        assert updated_group.id == "group_id"
        assert updated_group.name == "Test Group"
        assert updated_group.color == UserGroupColor.BLUE
        assert len(updated_group.users) == 1
        assert list(updated_group.users)[0].id == "user_id"
        assert len(updated_group.projects) == 1
        assert list(updated_group.projects)[0].id == "project_id"

    def test_create_with_exception_id(self):
        group = self.group
        group.id = "group_id"

        with pytest.raises(ResourceCreationError):
            group.create()

    def test_create_with_exception_name(self):
        group = self.group
        group.name = ""

        with pytest.raises(ValueError):
            group.create()

    def test_create(self):
        group = self.group
        group.name = "New Group"
        group.color = UserGroupColor.PINK
        group.users = {UserGroupUser(id="user_id", email="test@example.com")}
        group.projects = {
            UserGroupProject(id="project_id", name="Test Project")
        }

        self.client.execute.return_value = {
            "createUserGroup": {
                "group": {
                    "id": "group_id"
                }
            }
        }
        created_group = group.create()
        execute = self.client.execute.call_args[0]

        assert "CreateUserGroupPyApi" in execute[0]
        assert execute[1]["name"] == "New Group"
        assert execute[1]["color"] == UserGroupColor.PINK.value
        assert len(execute[1]["userIds"]) == 1
        assert list(execute[1]["userIds"])[0] == "user_id"
        assert len(execute[1]["projectIds"]) == 1
        assert list(execute[1]["projectIds"])[0] == "project_id"
        assert created_group.id is not None
        assert created_group.id == "group_id"
        assert created_group.name == "New Group"
        assert created_group.color == UserGroupColor.PINK
        assert len(created_group.users) == 1
        assert list(created_group.users)[0].id == "user_id"
        assert len(created_group.projects) == 1
        assert list(created_group.projects)[0].id == "project_id"

    def test_delete(self):
        group = self.group
        group.id = "group_id"

        self.client.execute.return_value = {
            "deleteUserGroup": {
                "success": True
            }
        }
        deleted = group.delete()
        execute = self.client.execute.call_args[0]

        assert "DeleteUserGroupPyApi" in execute[0]
        assert execute[1]["id"] == "group_id"
        assert deleted is True

    def test_user_groups_empty(self):
        self.client.execute.return_value = {"userGroups": None}

        user_groups = list(UserGroup.get_user_groups(self.client))

        assert len(user_groups) == 0

    def test_user_groups(self):
        self.client.execute.return_value = {
            "userGroups": {
                "nextCursor":
                    None,
                "nodes": [{
                    "id": "group_id_1",
                    "name": "Group 1",
                    "color": "9EC5FF",
                    "projects": {
                        "nodes": [{
                            "id": "project_id_1",
                            "name": "Project 1"
                        }, {
                            "id": "project_id_2",
                            "name": "Project 2"
                        }]
                    },
                    "members": {
                        "nodes": [{
                            "id": "user_id_1",
                            "email": "user1@example.com"
                        }, {
                            "id": "user_id_2",
                            "email": "user2@example.com"
                        }]
                    }
                }, {
                    "id": "group_id_2",
                    "name": "Group 2",
                    "color": "9EC5FF",
                    "projects": {
                        "nodes": [{
                            "id": "project_id_3",
                            "name": "Project 3"
                        }, {
                            "id": "project_id_4",
                            "name": "Project 4"
                        }]
                    },
                    "members": {
                        "nodes": [{
                            "id": "user_id_3",
                            "email": "user3@example.com"
                        }, {
                            "id": "user_id_4",
                            "email": "user4@example.com"
                        }]
                    }
                }, {
                    "id": "group_id_3",
                    "name": "Group 3",
                    "color": "9EC5FF",
                    "projects": {
                        "nodes": [{
                            "id": "project_id_5",
                            "name": "Project 5"
                        }, {
                            "id": "project_id_6",
                            "name": "Project 6"
                        }]
                    },
                    "members": {
                        "nodes": [{
                            "id": "user_id_5",
                            "email": "user5@example.com"
                        }, {
                            "id": "user_id_6",
                            "email": "user6@example.com"
                        }]
                    }
                }]
            }
        }

        user_groups = list(UserGroup.get_user_groups(self.client))

        assert len(user_groups) == 3

        # Check the attributes of the first user group
        assert user_groups[0].id == "group_id_1"
        assert user_groups[0].name == "Group 1"
        assert user_groups[0].color == UserGroupColor.BLUE
        assert len(user_groups[0].projects) == 2
        assert len(user_groups[0].users) == 2

        # Check the attributes of the second user group
        assert user_groups[1].id == "group_id_2"
        assert user_groups[1].name == "Group 2"
        assert user_groups[1].color == UserGroupColor.BLUE
        assert len(user_groups[1].projects) == 2
        assert len(user_groups[1].users) == 2

        # Check the attributes of the third user group
        assert user_groups[2].id == "group_id_3"
        assert user_groups[2].name == "Group 3"
        assert user_groups[2].color == UserGroupColor.BLUE
        assert len(user_groups[2].projects) == 2
        assert len(user_groups[2].users) == 2


if __name__ == "__main__":
    import subprocess
    subprocess.call(["pytest", "-v", __file__])
