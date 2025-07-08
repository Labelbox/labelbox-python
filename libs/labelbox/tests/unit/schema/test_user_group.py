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
    UserGroupMember,
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
    user = User(MagicMock(Client), user_values)
    # Mock org_role() to return None (project-based user)
    user.org_role = MagicMock(return_value=None)
    return user


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
        # Reset the global roles cache before each test
        import labelbox.schema.role as role_module

        role_module._ROLES = None

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
        assert len(self.group.members) == 0
        assert len(self.group.projects) == 0

    def test_constructor_with_members(self, group_user, mock_role):
        """Test that constructor works with members"""
        member = UserGroupMember(user=group_user, role=mock_role)
        group = UserGroup(
            client=self.client,
            name="Test Group",
            members={member},
        )
        assert group.name == "Test Group"
        assert len(group.members) == 1
        assert member in group.members

    def test_constructor_validation_error_invalid_member_role(self, group_user):
        """Test that constructor fails when UserGroupMember has invalid role"""
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
        self.client.execute.side_effect = [
            # Mock userGroupV2 query response first (get() executes this first)
            {
                "userGroupV2": {
                    "id": "group_id",
                    "name": "Test Group",
                    "color": "4ED2F9",
                    "description": "",
                    "projects": {
                        "nodes": projects,
                        "totalCount": 2,
                    },
                    "members": {
                        "nodes": group_members,
                        "totalCount": 2,
                        "userGroupRoles": [
                            {"userId": "user_id_1", "roleId": "role_id_1"},
                            {"userId": "user_id_2", "roleId": "role_id_2"},
                        ],
                    },
                }
            },
            # Mock get_roles query response second (_get_members_set calls this)
            {
                "roles": [
                    {"id": "role_id_1", "name": "LABELER"},
                    {"id": "role_id_2", "name": "REVIEWER"},
                ]
            },
        ]
        group = UserGroup(self.client)
        assert group.id == ""
        assert group.name == ""
        assert group.color is UserGroupColor.BLUE
        assert len(group.projects) == 0
        assert len(group.members) == 0

        group.id = "group_id"
        group.get()

        assert group.id == "group_id"
        assert group.name == "Test Group"
        assert group.color is UserGroupColor.CYAN
        assert len(group.projects) == 2
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
        group.members = {UserGroupMember(user=group_user, role=mock_role)}
        group.projects = {group_project}

        # Mock the additional methods that make client.execute calls
        self.client.get_project.return_value = group_project

        self.client.execute.side_effect = [
            # Mock update mutation response
            {
                "updateUserGroupV3": {
                    "group": {
                        "id": "group_id",
                        "name": "Test Group",
                        "description": "",
                        "updatedAt": "2023-01-01T00:00:00Z",
                        "createdByUserName": "test",
                    }
                }
            },
            # Mock get query response after update (get() executes userGroupV2 first)
            {
                "userGroupV2": {
                    "id": "group_id",
                    "name": "Test Group",
                    "color": "9EC5FF",
                    "description": "",
                    "projects": {
                        "nodes": [{"id": "project_id", "name": "Test Project"}],
                        "totalCount": 1,
                    },
                    "members": {
                        "nodes": [
                            {
                                "id": "user_id",
                                "email": "test@example.com",
                                "orgRole": None,
                            }
                        ],
                        "totalCount": 1,
                        "userGroupRoles": [
                            {"userId": "user_id", "roleId": "role_id"}
                        ],
                    },
                }
            },
            # Mock get_roles query response (called by _get_members_set)
            {
                "roles": [
                    {"id": "role_id", "name": "LABELER"},
                ]
            },
        ]

        group.update()

        assert group.name == "Test Group"

    def test_update_without_members_should_work(self, group_project):
        """Test that update works when members field is empty"""
        group = UserGroup(self.client)
        group.id = "group_id"
        group.name = "Test Group"
        group.projects = {group_project}

        self.client.get_project.return_value = group_project
        self.client.execute.side_effect = [
            # Mock update mutation response
            {
                "updateUserGroupV3": {
                    "group": {
                        "id": "group_id",
                        "name": "Test Group",
                        "description": "",
                        "updatedAt": "2023-01-01T00:00:00Z",
                        "createdByUserName": "test",
                    }
                }
            },
            # Mock get query response (get() executes userGroupV2 first)
            {
                "userGroupV2": {
                    "id": "group_id",
                    "name": "Test Group",
                    "color": "9EC5FF",
                    "description": "",
                    "projects": {
                        "nodes": [{"id": "project_id", "name": "Test Project"}],
                        "totalCount": 1,
                    },
                    "members": {
                        "nodes": [],
                        "totalCount": 0,
                        "userGroupRoles": [],
                    },
                }
            },
            # Mock get_roles query response (even though no members, _get_members_set is still called)
            {"roles": []},
        ]

        group.update()
        assert group.name == "Test Group"

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
            "userGroupsV2": {
                "totalCount": 0,
                "nextCursor": None,
                "nodes": [],
            }
        }
        user_groups = list(UserGroup.get_user_groups(self.client))
        assert len(user_groups) == 0

    def test_user_groups(self):
        # Mock get_user_groups and get_roles responses
        # The order is: userGroupsV2 query first, then get_roles when processing groups
        self.client.execute.side_effect = [
            # get_user_groups query (first)
            {
                "userGroupsV2": {
                    "totalCount": 2,
                    "nextCursor": None,
                    "nodes": [
                        {
                            "id": "group_id_1",
                            "name": "Group 1",
                            "color": "9EC5FF",
                            "description": "",
                            "projects": {
                                "nodes": [],
                                "totalCount": 0,
                            },
                            "members": {
                                "nodes": [],
                                "totalCount": 0,
                                "userGroupRoles": [],
                            },
                        },
                        {
                            "id": "group_id_2",
                            "name": "Group 2",
                            "color": "CEB8FF",
                            "description": "",
                            "projects": {
                                "nodes": [],
                                "totalCount": 0,
                            },
                            "members": {
                                "nodes": [],
                                "totalCount": 0,
                                "userGroupRoles": [],
                            },
                        },
                    ],
                }
            },
            # get_roles query (called when processing first group, then cached)
            {"roles": []},
        ]
        user_groups = list(UserGroup.get_user_groups(self.client))
        assert len(user_groups) == 2
        assert user_groups[0].name == "Group 1"
        assert user_groups[1].name == "Group 2"

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

    def test_create(self, group_user, group_project, mock_role):
        group = self.group
        group.name = "Test Group"
        group.color = UserGroupColor.BLUE
        group.members = {UserGroupMember(user=group_user, role=mock_role)}
        group.projects = {group_project}

        # Mock the additional methods that make client.execute calls
        self.client.get_project.return_value = group_project

        self.client.execute.side_effect = [
            # Mock create mutation response
            {
                "createUserGroupV3": {
                    "group": {
                        "id": "group_id",
                        "name": "Test Group",
                        "description": "",
                        "updatedAt": "2023-01-01T00:00:00Z",
                        "createdByUserName": "test",
                    }
                }
            },
            # Mock get query response after create (get() executes userGroupV2 first)
            {
                "userGroupV2": {
                    "id": "group_id",
                    "name": "Test Group",
                    "color": "9EC5FF",
                    "description": "",
                    "projects": {
                        "nodes": [{"id": "project_id", "name": "Test Project"}],
                        "totalCount": 1,
                    },
                    "members": {
                        "nodes": [
                            {
                                "id": "user_id",
                                "email": "test@example.com",
                                "orgRole": None,
                            }
                        ],
                        "totalCount": 1,
                        "userGroupRoles": [
                            {"userId": "user_id", "roleId": "role_id"}
                        ],
                    },
                }
            },
            # Mock get_roles query response (called by _get_members_set)
            {
                "roles": [
                    {"id": "role_id", "name": "LABELER"},
                ]
            },
        ]

        group.create()
        assert group.id == "group_id"
        assert group.name == "Test Group"
        assert group.color == UserGroupColor.BLUE

    def test_create_without_members_should_work(self, group_project):
        """Test that create works when members field is empty"""
        group = self.group
        group.name = "Test Group"
        group.projects = {group_project}

        self.client.get_project.return_value = group_project
        self.client.execute.side_effect = [
            # Mock create mutation response
            {
                "createUserGroupV3": {
                    "group": {
                        "id": "group_id",
                        "name": "Test Group",
                        "description": "",
                        "updatedAt": "2023-01-01T00:00:00Z",
                        "createdByUserName": "test",
                    }
                }
            },
            # Mock get query response (get() executes userGroupV2 first)
            {
                "userGroupV2": {
                    "id": "group_id",
                    "name": "Test Group",
                    "color": "9EC5FF",
                    "description": "",
                    "projects": {
                        "nodes": [{"id": "project_id", "name": "Test Project"}],
                        "totalCount": 1,
                    },
                    "members": {
                        "nodes": [],
                        "totalCount": 0,
                        "userGroupRoles": [],
                    },
                }
            },
            # Mock get_roles query response (even though no members, _get_members_set is still called)
            {"roles": []},
        ]

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

    def test_user_group_member_invalid_role_validation(self, group_user):
        """Test that UserGroupMember fails with invalid roles"""
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

    # Mock responses for both create mutation and get query
    client.execute.side_effect = [
        # First call: create mutation
        {
            "createUserGroupV3": {
                "group": {
                    "id": "group_id",
                    "name": "Test Group",
                    "description": "Test description",
                    "updatedAt": "2023-01-01T00:00:00Z",
                    "createdByUserName": "Test User",
                }
            }
        },
        # Second call: get query (get() executes userGroupV2 first)
        {
            "userGroupV2": {
                "id": "group_id",
                "name": "Test Group",
                "color": "9EC5FF",
                "description": "Test description",
                "projects": {"nodes": [], "totalCount": 0},
                "members": {"nodes": [], "totalCount": 0, "userGroupRoles": []},
            }
        },
        # Third call: get_roles query (called by _get_members_set)
        {"roles": []},
    ]

    group.create()

    # Verify the mutation was called
    assert client.execute.called
    # Check the first call (create mutation)
    first_call_args = client.execute.call_args_list[0]
    query = first_call_args[0][0]
    params = first_call_args[0][1]

    assert "createUserGroupV3" in query
    # Verify parameters match new field ordering
    assert params["name"] == "Test Group"
    assert params["description"] == "Test description"
    assert params["color"] == "9EC5FF"
    assert params["notifyMembers"] is True

    # Verify parameter order in query (standardized field order)
    expected_param_pattern = "$name: String!, $description: String, $color: String!, $projectIds: [ID!]!, $userRoles: [UserRoleInput!]!, $notifyMembers: Boolean, $roleId: String, $searchQuery: AlignerrSearchServiceQuery"
    assert expected_param_pattern.replace(" ", "") in query.replace(" ", "")


def test_update_mutation():
    """Test the update mutation structure."""
    client = MagicMock(Client)

    group = UserGroup(client)
    group.id = "group_id"
    group.name = "Updated Group"
    group.description = "Updated description"
    group.color = UserGroupColor.PURPLE

    # Mock responses for both update mutation and get query
    client.execute.side_effect = [
        # First call: update mutation
        {
            "updateUserGroupV3": {
                "group": {
                    "id": "group_id",
                    "name": "Updated Group",
                    "description": "Updated description",
                    "updatedAt": "2023-01-01T00:00:00Z",
                    "createdByUserName": "Test User",
                }
            }
        },
        # Second call: get query (get() executes userGroupV2 first)
        {
            "userGroupV2": {
                "id": "group_id",
                "name": "Updated Group",
                "color": "CEB8FF",
                "description": "Updated description",
                "projects": {"nodes": [], "totalCount": 0},
                "members": {"nodes": [], "totalCount": 0, "userGroupRoles": []},
            }
        },
        # Third call: get_roles query (called by _get_members_set)
        {"roles": []},
    ]

    group.update()

    # Verify the mutation was called
    assert client.execute.called
    # Check the first call (update mutation)
    first_call_args = client.execute.call_args_list[0]
    query = first_call_args[0][0]
    params = first_call_args[0][1]

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
