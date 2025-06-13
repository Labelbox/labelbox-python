"""Unit tests for UserGroup functionality.

Note: UserGroup members cannot have certain roles:
- "NONE" (project-based role) - Users with this role cannot be added to UserGroups
- "TENANT_ADMIN" - This role cannot be used in UserGroups
Valid roles for UserGroups include: LABELER, REVIEWER, TEAM_MANAGER, ADMIN, PROJECT_LEAD, etc.
"""

from collections import defaultdict
from unittest.mock import MagicMock

import pytest
from lbox.exceptions import (
    ResourceConflict,
    ResourceCreationError,
    ResourceNotFoundError,
    UnprocessableEntityError,
)

from labelbox import Client
from labelbox.schema.media_type import MediaType
from labelbox.schema.ontology_kind import EditorTaskType
from labelbox.schema.project import Project
from labelbox.schema.user import User
from labelbox.schema.user_group import (
    UserGroup,
    UserGroupColor,
    INVALID_USERGROUP_ROLES,
)
from labelbox.schema.role import Role


@pytest.fixture
def group_user():
    user_values = defaultdict(lambda: None)
    user_values["id"] = "user_id"
    user_values["email"] = "test@example.com"
    user_values["name"] = "Test User"
    user_values["nickname"] = "testuser"
    user_values["createdAt"] = "2023-01-01T00:00:00Z"
    user_values["isExternalUser"] = False
    user_values["isViewer"] = False
    return User(MagicMock(Client), user_values)


@pytest.fixture
def group_project():
    project_values = defaultdict(lambda: None)
    project_values["id"] = "project_id"
    project_values["name"] = "Test Project"
    project_values["editorTaskType"] = EditorTaskType.Missing.value
    project_values["mediaType"] = MediaType.Image.value
    return Project(MagicMock(Client), project_values)


@pytest.fixture
def mock_role():
    """Create a mock Role object for testing."""
    role_values = defaultdict(lambda: None)
    role_values["id"] = "role_id"
    role_values["name"] = (
        "LABELER"  # Use a valid role that can be assigned to UserGroups
    )
    return Role(MagicMock(Client), role_values)


@pytest.fixture
def client_mock():
    """Create a mock client for testing."""
    from labelbox import Client

    return MagicMock(spec=Client)


@pytest.fixture
def roles_mock(client_mock):
    """Create mock roles for testing."""
    return {
        "LABELER": Role(client_mock, {"id": "labeler_id", "name": "LABELER"}),
        "ADMIN": Role(client_mock, {"id": "admin_id", "name": "ADMIN"}),
        "REVIEWER": Role(
            client_mock, {"id": "reviewer_id", "name": "REVIEWER"}
        ),
    }


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


class TestUserGroup:
    def setup_method(self):
        self.client = MagicMock(Client)
        self.client.get_roles.return_value = {
            "LABELER": Role(self.client, {"id": "role_id", "name": "LABELER"}),
            "ADMIN": Role(self.client, {"id": "admin_id", "name": "ADMIN"}),
            "REVIEWER": Role(
                self.client, {"id": "reviewer_id", "name": "REVIEWER"}
            ),
        }
        self.group = UserGroup(self.client)

    def test_constructor(self):
        assert self.group.name == ""
        assert self.group.color is UserGroupColor.BLUE
        assert len(self.group.users) == 0
        assert len(self.group.members) == 0
        assert len(self.group.projects) == 0

    def test_constructor_validation_error_users_without_default_role(
        self, group_user
    ):
        """Test that constructor fails when users are provided but default_role is None"""
        from pydantic import ValidationError

        with pytest.raises(
            ValidationError,
            match="default_role must be set when using the 'users' field",
        ):
            UserGroup(
                client=self.client,
                name="Test Group",
                users={group_user},
                # default_role not provided - should raise ValueError
            )

    def test_constructor_with_users_and_default_role(
        self, group_user, mock_role
    ):
        """Test that constructor works when both users and default_role are provided"""
        group = UserGroup(
            client=self.client,
            name="Test Group",
            users={group_user},
            default_role=mock_role,
        )
        assert group.name == "Test Group"
        assert len(group.users) == 1
        assert group.default_role == mock_role

    def test_constructor_validation_error_invalid_default_role(self):
        """Test that constructor fails when default_role is NONE or TENANT_ADMIN"""

        # Test each invalid role
        for invalid_role_name in INVALID_USERGROUP_ROLES:
            # Create a proper Role object with invalid name
            role_values = defaultdict(lambda: None)
            role_values["id"] = f"{invalid_role_name.lower()}_role_id"
            role_values["name"] = invalid_role_name
            invalid_role = Role(self.client, role_values)

            with pytest.raises(
                ValueError,
                match=f"default_role cannot be '{invalid_role_name}'",
            ):
                UserGroup(
                    client=self.client,
                    name="Test Group",
                    default_role=invalid_role,
                )

    def test_update_with_exception_name(self):
        group = self.group
        group.name = ""
        with pytest.raises(ValueError):
            group.update()

    def test_get(self):
        projects = [
            {"id": "project_id_1", "name": "project_1"},
            {"id": "project_id_2", "name": "project_2"},
        ]
        group_members = [
            {
                "id": "user_id_1",
                "email": "email_1",
                "orgRole": {"id": "role_id_1", "name": "LABELER"},
            },
            {
                "id": "user_id_2",
                "email": "email_2",
                "orgRole": {"id": "role_id_2", "name": "LABELER"},
            },
        ]
        self.client.execute.return_value = {
            "userGroup": {
                "id": "group_id",
                "name": "Test Group",
                "color": "4ED2F9",
                "description": "",
                "projects": {
                    "nodes": projects,
                    "pageInfo": {"hasNextPage": False},
                },
                "members": {
                    "nodes": group_members,
                    "pageInfo": {"hasNextPage": False},
                },
            }
        }
        group = UserGroup(self.client)
        assert group.id == ""
        assert group.name == ""
        assert group.color is UserGroupColor.BLUE
        assert len(group.projects) == 0
        assert len(group.users) == 0
        assert len(group.members) == 0

        group.id = "group_id"
        # Set default_role so that members can be created from response
        roles = self.client.get_roles.return_value
        group.default_role = roles["LABELER"]
        group.get()

        assert group.id == "group_id"
        assert group.name == "Test Group"
        assert group.color is UserGroupColor.CYAN
        assert len(group.projects) == 2
        assert len(group.users) == 0
        assert len(group.members) == 2

    def test_get_value_error(self):
        self.client.execute.return_value = None
        group = UserGroup(self.client)
        group.name = "Test Group"
        with pytest.raises(ValueError):
            group.get()

    def test_update(self, group_user, group_project, mock_role):
        group = self.group
        group.id = "group_id"
        group.name = "Test Group"
        group.color = UserGroupColor.BLUE
        group.users = {group_user}
        group.projects = {group_project}
        group.default_role = mock_role

        self.client.execute.return_value = {
            "updateUserGroupV3": {
                "group": {
                    "id": "group_id",
                    "name": "Test Group",
                    "color": "9EC5FF",
                    "description": "",
                    "projects": {
                        "nodes": [{"id": "project_id", "name": "Test Project"}],
                        "pageInfo": {"hasNextPage": False},
                    },
                    "members": {
                        "nodes": [
                            {
                                "id": "user_id",
                                "email": "test@example.com",
                                "orgRole": {"id": "role_id", "name": "LABELER"},
                            }
                        ],
                        "pageInfo": {"hasNextPage": False},
                    },
                }
            }
        }

        updated_group = group.update()
        assert updated_group.id == "group_id"
        assert updated_group.name == "Test Group"
        assert updated_group.color == UserGroupColor.BLUE

    def test_update_validation_error_no_default_role(self, group_user):
        """Test that update fails when users field is set but default_role is None"""
        group = self.group
        group.id = "group_id"
        group.name = "Test Group"
        group.users = {group_user}
        # Don't set default_role - should raise ValueError

        with pytest.raises(
            ValueError,
            match="default_role must be set when using the 'users' field",
        ):
            group.update()

    def test_update_without_users_no_default_role_required(self, group_project):
        """Test that update works when users field is empty and no default_role is set"""
        group = self.group
        group.id = "group_id"
        group.name = "Test Group"
        group.projects = {group_project}
        # Don't set users or default_role - should work fine

        self.client.execute.return_value = {
            "updateUserGroupV3": {
                "group": {
                    "id": "group_id",
                    "name": "Test Group",
                    "color": "9EC5FF",
                    "description": "",
                    "projects": {
                        "nodes": [{"id": "project_id", "name": "Test Project"}],
                        "pageInfo": {"hasNextPage": False},
                    },
                    "members": {
                        "nodes": [],
                        "pageInfo": {"hasNextPage": False},
                    },
                }
            }
        }

        updated_group = group.update()
        assert updated_group.id == "group_id"
        assert updated_group.name == "Test Group"

    def test_update_resource_error_input_bad(self):
        self.client.execute.side_effect = UnprocessableEntityError("Bad input")
        group = self.group
        group.id = "group_id"
        group.name = "Test Group"
        with pytest.raises(UnprocessableEntityError):
            group.update()

    def test_update_resource_error_unknown_id(self):
        self.client.execute.side_effect = ResourceNotFoundError(
            message="Unknown ID"
        )
        group = self.group
        group.id = "group_id"
        group.name = "Test Group"
        with pytest.raises(ResourceNotFoundError):
            group.update()

    def test_update_with_exception_name(self):
        group = self.group
        group.id = "group_id"
        group.name = ""
        with pytest.raises(ValueError):
            group.update()

    def test_update_with_exception_id(self):
        group = self.group
        group.id = ""
        group.name = "Test Group"
        with pytest.raises(ValueError):
            group.update()

    def test_create(self, group_user, group_project, mock_role):
        group = self.group
        group.name = "Test Group"
        group.color = UserGroupColor.BLUE
        group.users = {group_user}
        group.projects = {group_project}
        # Must explicitly set default_role when using users field
        group.default_role = mock_role

        self.client.execute.return_value = {
            "createUserGroupV3": {
                "group": {
                    "id": "group_id",
                    "name": "Test Group",
                    "color": "9EC5FF",
                    "description": "",
                    "projects": {
                        "nodes": [{"id": "project_id", "name": "Test Project"}],
                        "pageInfo": {"hasNextPage": False},
                    },
                    "members": {
                        "nodes": [
                            {
                                "id": "user_id",
                                "email": "test@example.com",
                                "orgRole": {"id": "role_id", "name": "LABELER"},
                            }
                        ],
                        "pageInfo": {"hasNextPage": False},
                    },
                }
            }
        }

        group.create()
        assert group.id == "group_id"
        assert group.name == "Test Group"
        assert group.color == UserGroupColor.BLUE

    def test_create_validation_error_no_default_role(self, group_user):
        """Test that create fails when users field is set but default_role is None"""
        group = self.group
        group.name = "Test Group"
        group.users = {group_user}
        # Don't set default_role - should raise ValueError

        with pytest.raises(
            ValueError,
            match="default_role must be explicitly set when using the 'users' field",
        ):
            group.create()

    def test_create_without_users_no_default_role_required(self, group_project):
        """Test that create works when users field is empty and no default_role is set"""
        group = self.group
        group.name = "Test Group"
        group.projects = {group_project}
        # Don't set users or default_role - should work fine

        self.client.execute.return_value = {
            "createUserGroupV3": {
                "group": {
                    "id": "group_id",
                    "name": "Test Group",
                    "color": "9EC5FF",
                    "description": "",
                    "projects": {
                        "nodes": [{"id": "project_id", "name": "Test Project"}],
                        "pageInfo": {"hasNextPage": False},
                    },
                    "members": {
                        "nodes": [],
                        "pageInfo": {"hasNextPage": False},
                    },
                }
            }
        }

        group.create()
        assert group.id == "group_id"
        assert group.name == "Test Group"

    def test_create_with_exception_id(self):
        """Test that create fails when group already has an ID"""
        group = self.group
        group.id = "group_id"
        group.name = "Test Group"
        with pytest.raises(ValueError):
            group.create()

    def test_create_with_exception_name(self):
        """Test that create fails when group name is empty"""
        group = self.group
        group.name = ""
        with pytest.raises(ValueError):
            group.create()

    def test_create_resource_creation_error(self):
        self.client.execute.side_effect = ResourceConflict("Conflict")
        group = self.group
        group.name = "Test Group"
        with pytest.raises(ResourceCreationError):
            group.create()

    def test_delete(self):
        self.client.execute.return_value = {
            "deleteUserGroup": {"success": True}
        }
        group = self.group
        group.id = "group_id"
        result = group.delete()
        assert result is True

    def test_delete_resource_not_found_error(self):
        self.client.execute.side_effect = ResourceNotFoundError(
            message="Not found"
        )
        group = self.group
        group.id = "group_id"
        with pytest.raises(ResourceNotFoundError):
            group.delete()

    def test_delete_no_id(self):
        group = self.group
        group.id = ""
        with pytest.raises(ValueError):
            group.delete()

    def test_user_groups_empty(self):
        self.client.execute.return_value = {
            "userGroups": {
                "nodes": [],
                "pageInfo": {"hasNextPage": False, "endCursor": None},
            }
        }
        user_groups = list(UserGroup.get_user_groups(self.client))
        assert len(user_groups) == 0

    def test_user_groups(self):
        self.client.execute.return_value = {
            "userGroups": {
                "nodes": [
                    {
                        "id": "group_id_1",
                        "name": "Group 1",
                        "color": "9EC5FF",
                        "description": "",
                        "projects": {
                            "nodes": [],
                            "pageInfo": {"hasNextPage": False},
                        },
                        "members": {
                            "nodes": [],
                            "pageInfo": {"hasNextPage": False},
                        },
                    },
                    {
                        "id": "group_id_2",
                        "name": "Group 2",
                        "color": "CEB8FF",
                        "description": "",
                        "projects": {
                            "nodes": [],
                            "pageInfo": {"hasNextPage": False},
                        },
                        "members": {
                            "nodes": [],
                            "pageInfo": {"hasNextPage": False},
                        },
                    },
                ],
                "pageInfo": {"hasNextPage": False, "endCursor": None},
            }
        }
        user_groups = list(UserGroup.get_user_groups(self.client))
        assert len(user_groups) == 2
        assert user_groups[0].name == "Group 1"
        assert user_groups[1].name == "Group 2"

    def test_user_group_member_invalid_role_validation(self, group_user):
        """Test that UserGroupMember fails with invalid roles"""
        from labelbox.schema.user_group import UserGroupMember

        # Test each invalid role
        for invalid_role_name in INVALID_USERGROUP_ROLES:
            # Create a proper Role object with invalid name
            role_values = defaultdict(lambda: None)
            role_values["id"] = f"{invalid_role_name.lower()}_role_id"
            role_values["name"] = invalid_role_name
            invalid_role = Role(self.client, role_values)

            with pytest.raises(
                ValueError,
                match=f"Role '{invalid_role_name}' cannot be assigned to UserGroup members",
            ):
                UserGroupMember(user=group_user, role=invalid_role)


def test_create_mutation():
    """Test the create mutation structure."""
    client = MagicMock(Client)

    group = UserGroup(client)
    group.name = "Test Group"
    group.description = "Test description"
    group.color = UserGroupColor.BLUE
    group.notify_members = True

    client.execute.return_value = {
        "createUserGroupV3": {
            "group": {
                "id": "group_id",
                "name": "Test Group",
                "color": "9EC5FF",
                "description": "Test description",
                "projects": {"nodes": []},
                "members": {"nodes": []},
            }
        }
    }

    group.create()

    # Verify the mutation was called
    assert client.execute.called
    call_args = client.execute.call_args
    query = call_args[0][0]
    params = call_args[0][1]

    assert "createUserGroupV3" in query
    # Verify parameters match new field ordering
    assert params["name"] == "Test Group"
    assert params["description"] == "Test description"
    assert params["color"] == "9EC5FF"
    assert params["notifyMembers"] is True

    # Verify parameter order in query (standardized field order)
    expected_param_pattern = "$name: String!, $description: String, $color: String!, $projectIds: [ID!], $userRoles: [UserRoleInput!], $notifyMembers: Boolean, $roleId: String, $searchQuery: AlignerrSearchServiceQuery"
    assert expected_param_pattern.replace(" ", "") in query.replace(" ", "")


def test_update_mutation():
    """Test the update mutation structure."""
    client = MagicMock(Client)

    group = UserGroup(client)
    group.id = "group_id"
    group.name = "Updated Group"
    group.description = "Updated description"
    group.color = UserGroupColor.PURPLE

    client.execute.return_value = {
        "updateUserGroupV3": {
            "group": {
                "id": "group_id",
                "name": "Updated Group",
                "color": "CEB8FF",
                "description": "Updated description",
                "projects": {"nodes": []},
                "members": {"nodes": []},
            }
        }
    }

    group.update()

    # Verify the mutation was called
    assert client.execute.called
    call_args = client.execute.call_args
    query = call_args[0][0]
    params = call_args[0][1]

    assert "updateUserGroupV3" in query
    # Verify parameters match new field ordering
    assert params["id"] == "group_id"
    assert params["name"] == "Updated Group"
    assert params["description"] == "Updated description"
    assert params["color"] == "CEB8FF"

    # Verify parameter order in query (standardized field order)
    expected_param_pattern = "$id: ID!, $name: String!, $description: String, $color: String!, $projectIds: [ID!]!, $userRoles: [UserRoleInput!], $notifyMembers: Boolean"
    assert expected_param_pattern.replace(" ", "") in query.replace(" ", "")


def test_create_error_handling():
    """Test error handling during create."""
    client = MagicMock(Client)
    client.get_roles.return_value = {
        "LABELER": Role(client, {"id": "role_id", "name": "LABELER"}),
    }

    group = UserGroup(client)
    group.name = "Test Group"

    # Test ResourceConflict -> ResourceCreationError
    client.execute.side_effect = ResourceConflict("Group exists")
    with pytest.raises(ResourceCreationError):
        group.create()

    # Test UnprocessableEntityError handling
    client.execute.side_effect = UnprocessableEntityError("Invalid data")
    with pytest.raises(ResourceCreationError):
        group.create()


def test_update_error_handling():
    """Test error handling during update."""
    client = MagicMock(Client)
    client.get_roles.return_value = {
        "LABELER": Role(client, {"id": "role_id", "name": "LABELER"}),
    }

    group = UserGroup(client)
    group.id = "group_id"
    group.name = "Test Group"

    # Test UnprocessableEntityError handling
    client.execute.side_effect = UnprocessableEntityError("Invalid data")
    with pytest.raises(UnprocessableEntityError):
        group.update()

    # Test ResourceNotFoundError handling
    client.execute.side_effect = ResourceNotFoundError(message="Not found")
    with pytest.raises(ResourceNotFoundError):
        group.update()
