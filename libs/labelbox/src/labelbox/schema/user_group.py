"""UserGroup implementation for Labelbox Python SDK.

This module provides the UserGroup class and related functionality for managing
user groups in Labelbox.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Iterator, List, Optional, Set

from lbox.exceptions import (
    InvalidQueryError,
    MalformedQueryException,
    ResourceConflict,
    ResourceCreationError,
    ResourceNotFoundError,
    UnprocessableEntityError,
)
from pydantic import BaseModel, ConfigDict, Field

from labelbox import Client
from labelbox.schema.media_type import MediaType
from labelbox.schema.ontology_kind import EditorTaskType
from labelbox.schema.project import Project
from labelbox.schema.role import Role
from labelbox.schema.user import User

# Constants for UserGroup role restrictions
INVALID_USERGROUP_ROLES = frozenset(["NONE", "TENANT_ADMIN"])
"""Roles that cannot be assigned to UserGroup members.

- NONE: Project-based role
- TENANT_ADMIN: Special Administrative role
"""


@dataclass(eq=False)
class UserGroupMember:
    """Represents a user with their role in a user group.

    This class encapsulates the relationship between a user and their assigned
    role within a specific user group.

    Attributes:
        user: The User object representing the group member.
        role: The Role object representing the user's role in the group.
    """

    user: User
    role: Role

    def __hash__(self) -> int:
        """Generate hash based on user and role IDs.

        Returns:
            Hash value for the UserGroupMember instance.
        """
        return hash((self.user.uid, self.role.uid))

    def __eq__(self, other: object) -> bool:
        """Check equality based on user and role IDs.

        Args:
            other: Object to compare with.

        Returns:
            True if both user and role IDs match, False otherwise.
        """
        if not isinstance(other, UserGroupMember):
            return False
        return (
            self.user.uid == other.user.uid and self.role.uid == other.role.uid
        )

    def __post_init__(self) -> None:
        """Validate that the role is allowed for UserGroup members.

        Raises:
            ValueError: If the role is not allowed in UserGroups.
        """
        if self.role and hasattr(self.role, "name"):
            role_name = self.role.name.upper() if self.role.name else ""
            if role_name in INVALID_USERGROUP_ROLES:
                raise ValueError(
                    f"Role '{role_name}' cannot be assigned to UserGroup members. "
                    f"UserGroup members cannot have '{role_name}' roles."
                )


class UserGroupColor(Enum):
    """Enum representing the available colors for user groups.

    Each color is represented by its hex color code value.
    """

    BLUE = "9EC5FF"
    PURPLE = "CEB8FF"
    ORANGE = "FFB35F"
    CYAN = "4ED2F9"
    PINK = "FFAEA9"
    LIGHT_PINK = "FFA9D5"
    GREEN = "3FDC9A"
    YELLOW = "E7BF00"
    GRAY = "B8C4D3"


class UserGroup(BaseModel):
    """Represents a user group in Labelbox.

    UserGroups allow organizing users and projects together for access control
    and collaboration. Each user is added with an explicit role via UserGroupMember.

    Attributes:
        id: Unique identifier for the user group.
        name: Display name of the user group.
        color: Visual color identifier for the group.
        description: Optional description of the group's purpose.
        notify_members: Whether to notify members of group changes.
        members: Set of UserGroupMember objects with explicit roles.
        projects: Set of projects associated with this group.
        client: Labelbox client instance for API communication.

    Note:
        Only users with no organization role (orgRole: null) can be added to
        UserGroups. Users with any organization role will be rejected.
    """

    id: str
    name: str
    color: UserGroupColor
    description: str = ""
    notify_members: bool = False
    members: Set[UserGroupMember] = Field(default_factory=set)
    projects: Set[Project] = Field(default_factory=set)
    client: Client
    model_config = ConfigDict(arbitrary_types_allowed=True)

    def __init__(
        self,
        client: Client,
        id: str = "",
        name: str = "",
        color: UserGroupColor = UserGroupColor.BLUE,
        description: str = "",
        notify_members: bool = False,
        members: Optional[Set[UserGroupMember]] = None,
        projects: Optional[Set[Project]] = None,
    ) -> None:
        """Initialize a UserGroup instance.

        Args:
            client: Labelbox client for API communication.
            id: Unique identifier (empty for new groups).
            name: Display name for the group.
            color: Visual color identifier.
            description: Optional description.
            notify_members: Whether to notify members of changes.
            members: Set of members with explicit roles.
            projects: Set of associated projects.
        """
        super().__init__(
            client=client,
            id=id,
            name=name,
            color=color,
            description=description,
            notify_members=notify_members,
            members=members or set(),
            projects=projects or set(),
        )

    def get(self) -> UserGroup:
        """Reload the user group information from the server.

        Returns:
            Self with updated information from the server.

        Raises:
            ValueError: If group ID is not set.
            ResourceNotFoundError: If the group is not found on the server.
        """
        if not self.id:
            raise ValueError("Group id is required")

        query = """
            query GetUserGroupPyApi($id: ID!) {
                userGroupV2(where: {id: $id}) {
                    id
                    name
                    color
                    description
                    projects {
                        nodes { id name }
                        totalCount
                    }
                    members {
                        nodes {
                            id
                            email
                            orgRole { id name }
                        }
                        totalCount
                        userGroupRoles {
                            userId
                            roleId
                        }
                    }
                }
            }
        """

        result = self.client.execute(query, {"id": self.id})
        if not result or not result.get("userGroupV2"):
            raise ResourceNotFoundError(message="User group not found")

        group_data = result["userGroupV2"]
        self._update_from_response(group_data)

        return self

    def update(self) -> UserGroup:
        """Update the group in Labelbox.

        Returns:
            Self with updated information from the server.

        Raises:
            ValueError: If group ID or name is not set, or if projects don't exist.
            ResourceNotFoundError: If the group or projects are not found.
            UnprocessableEntityError: If user validation fails or users have workspace-level org roles.
        """
        if not self.id:
            raise ValueError("Group id is required")
        if not self.name:
            raise ValueError("Group name is required")

        # Validate projects exist
        for project in self.projects:
            try:
                self.client.get_project(project.uid)
            except ResourceNotFoundError:
                raise ValueError(
                    f"Project {project.uid} not found or inaccessible"
                )

        # Filter eligible users and build user roles
        try:
            eligible_users = self._filter_project_based_users()
            user_roles = self._build_user_roles(eligible_users)
        except ValueError as e:
            raise UnprocessableEntityError(str(e)) from e

        query = """
        mutation UpdateUserGroupPyApi($id: ID!, $name: String!, $description: String, $color: String!, $projectIds: [ID!]!, $userRoles: [UserRoleInput!], $notifyMembers: Boolean) {
            updateUserGroupV3(
                where: { id: $id }
                data: {
                    name: $name
                    description: $description
                    color: $color
                    projectIds: $projectIds
                    userRoles: $userRoles
                    notifyMembers: $notifyMembers
                }
            ) {
                group {
                    id
                    name
                    description
                    updatedAt
                    createdByUserName
                }
            }
        }
        """

        params = {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "color": self.color.value,
            "projectIds": [project.uid for project in self.projects],
            "userRoles": user_roles,
            "notifyMembers": self.notify_members,
        }

        try:
            result = self.client.execute(query, params, experimental=True)
            if not result:
                raise ResourceNotFoundError("Failed to update user group")

            group_data = result["updateUserGroupV3"]["group"]
            # Update basic fields from mutation response
            self.name = group_data["name"]
            self.description = group_data.get("description", "")

            # Fetch complete group data including projects and members
            self.get()

        except MalformedQueryException as e:
            raise UnprocessableEntityError("Failed to update user group") from e
        except UnprocessableEntityError as e:
            self._handle_user_validation_error(e, "update")

        return self

    def create(self) -> UserGroup:
        """Create a new user group in Labelbox.

        Returns:
            Self with ID and updated information from the server.

        Raises:
            ValueError: If group already has ID, name is invalid, or projects don't exist.
            ResourceCreationError: If creation fails, user validation fails, or users have workspace-level org roles.
            ResourceConflict: If a group with the same name already exists.
        """
        if self.id:
            raise ValueError("Cannot create group with existing ID")
        if not self.name or not self.name.strip():
            raise ValueError("Group name is required")

        # Validate projects exist
        for project in self.projects:
            try:
                self.client.get_project(project.uid)
            except ResourceNotFoundError:
                raise ValueError(
                    f"Project {project.uid} not found or inaccessible"
                )

        # Filter eligible users and build user roles
        try:
            eligible_users = self._filter_project_based_users()
            user_roles = self._build_user_roles(eligible_users)
        except ValueError as e:
            raise ResourceCreationError(str(e)) from e

        query = """
        mutation CreateUserGroupPyApi($name: String!, $description: String, $color: String!, $projectIds: [ID!]!, $userRoles: [UserRoleInput!]!, $notifyMembers: Boolean, $roleId: String, $searchQuery: AlignerrSearchServiceQuery) {
            createUserGroupV3(
                data: {
                    name: $name
                    description: $description
                    color: $color
                    projectIds: $projectIds
                    userRoles: $userRoles
                    notifyMembers: $notifyMembers
                    roleId: $roleId
                    searchQuery: $searchQuery
                }
            ) {
                group {
                    id
                    name
                    description
                    updatedAt
                    createdByUserName
                }
            }
        }
        """

        params = {
            "name": self.name,
            "description": self.description,
            "color": self.color.value,
            "projectIds": [project.uid for project in self.projects],
            "userRoles": user_roles,
            "notifyMembers": self.notify_members,
        }

        try:
            result = self.client.execute(query, params, experimental=True)
        except ResourceConflict as e:
            raise ResourceCreationError(
                f"User group with name '{self.name}' already exists"
            ) from e
        except (UnprocessableEntityError, InvalidQueryError) as e:
            self._handle_user_validation_error(e, "create")
        except Exception as e:
            raise ResourceCreationError(
                f"Failed to create user group: {str(e)}"
            ) from e

        if not result:
            raise ResourceCreationError(
                "Failed to create user group - no response from server"
            )

        group_data = result["createUserGroupV3"]["group"]
        self.id = group_data["id"]
        # Update basic fields from mutation response
        self.name = group_data["name"]
        self.description = group_data.get("description", "")

        # Fetch complete group data including projects and members
        self.get()

        return self

    def delete(self) -> bool:
        """Delete the user group from Labelbox.

        Returns:
            True if deletion was successful.

        Raises:
            ValueError: If group ID is not set.
            ResourceNotFoundError: If the group is not found.
        """
        if not self.id:
            raise ValueError("Group id is required")

        query = """
        mutation DeleteUserGroupPyApi($id: ID!) {
            deleteUserGroup(where: {id: $id}) {
                success
            }
        }
        """

        result = self.client.execute(query, {"id": self.id})
        if not result:
            raise ResourceNotFoundError(
                message="Failed to delete user group as user group does not exist"
            )
        return result["deleteUserGroup"]["success"]

    @staticmethod
    def get_user_groups(
        client: Client, page_size: int = 100
    ) -> Iterator[UserGroup]:
        """Get all user groups from Labelbox with pagination support.

        Args:
            client: Labelbox client for API communication.
            page_size: Number of groups to fetch per page.

        Yields:
            UserGroup instances for each group found.
        """
        query = """
            query GetUserGroupsPyApi($first: PageSize, $after: String) {
                userGroupsV2(first: $first, after: $after) {
                    totalCount
                    nextCursor
                    nodes {
                        id
                        name
                        color
                        description
                        projects { nodes { id name } totalCount }
                        members { 
                            nodes { 
                                id 
                                email 
                                orgRole { id name }
                            } 
                            totalCount
                            userGroupRoles {
                                userId
                                roleId
                            }
                        }
                    }
                }
            }
        """

        cursor = None
        while True:
            variables = {"first": page_size}
            if cursor:
                variables["after"] = cursor

            result = client.execute(query, variables)
            if not result or not result.get("userGroupsV2"):
                break

            for group_data in result["userGroupsV2"]["nodes"]:
                user_group = UserGroup(client)
                user_group.id = group_data["id"]
                user_group.name = group_data["name"]
                user_group.color = UserGroupColor(group_data["color"])
                user_group.description = group_data.get("description", "")
                user_group.projects = user_group._get_projects_set(
                    group_data["projects"]["nodes"]
                )
                user_group.members = user_group._get_members_set(
                    group_data["members"]
                )
                yield user_group

            cursor = result["userGroupsV2"].get("nextCursor")
            if not cursor:
                break

    def _filter_project_based_users(self) -> Set[User]:
        """Filter users to only include users eligible for UserGroups.

        Only project-based users (org role "NONE") can be added to UserGroups.
        Users with any workspace-level organization role cannot be added.

        Returns:
            Set of users that are eligible to be added to the group.

        Raises:
            ValueError: If any user has a workspace-level organization role.
        """
        all_users = set()
        for member in self.members:
            all_users.add(member.user)

        if not all_users:
            return set()

        # Check each user's org role directly
        invalid_users = []
        eligible_users = set()

        for user in all_users:
            try:
                # Get the user's organization role directly
                org_role = user.org_role()
                if org_role is None or org_role.name.upper() == "NONE":
                    # Users with no org role or "NONE" role are project-based and eligible
                    eligible_users.add(user)
                else:
                    # Users with any workspace org role cannot be assigned to UserGroups
                    invalid_users.append(
                        {
                            "id": user.uid,
                            "email": getattr(user, "email", "unknown"),
                            "org_role": org_role.name,
                        }
                    )
            except Exception as e:
                # If we can't determine the user's role, treat as invalid for safety
                invalid_users.append(
                    {
                        "id": user.uid,
                        "email": getattr(user, "email", "unknown"),
                        "org_role": f"unknown (error: {str(e)})",
                    }
                )

        # Raise error if any invalid users found
        if invalid_users:
            error_details = []
            for user_info in invalid_users:
                error_details.append(
                    f"User {user_info['id']} ({user_info['email']}) has org role '{user_info['org_role']}'"
                )

            raise ValueError(
                f"Cannot create UserGroup with users who have organization roles. "
                f"Only project-based users (no org role or role 'NONE') can be assigned to UserGroups.\n"
                f"Invalid users:\n"
                + "\n".join(f"  • {detail}" for detail in error_details)
            )

        return eligible_users

    def _build_user_roles(
        self, eligible_users: Set[User]
    ) -> List[Dict[str, str]]:
        """Build user roles array for GraphQL mutation.

        Args:
            eligible_users: Set of users that passed project-based validation.

        Returns:
            List of user role dictionaries for the GraphQL mutation.
        """
        user_roles: List[Dict[str, str]] = []

        # Add members with their explicit roles
        for member in self.members:
            if member.user in eligible_users:
                user_roles.append(
                    {"userId": member.user.uid, "roleId": member.role.uid}
                )

        return user_roles

    def _update_from_response(self, group_data: Dict[str, Any]) -> None:
        """Update object state from server response.

        Args:
            group_data: Dictionary containing group data from GraphQL response.
        """
        self.name = group_data["name"]
        # Handle missing color field in V3 response
        if "color" in group_data:
            self.color = UserGroupColor(group_data["color"])
        self.description = group_data.get("description", "")
        # notifyMembers field is not available in GraphQL response, so we keep the current value
        self.projects = self._get_projects_set(group_data["projects"]["nodes"])
        self.members = self._get_members_set(group_data["members"])

    def _handle_user_validation_error(
        self, error: Exception, operation: str
    ) -> None:
        """Handle user validation errors with helpful messages.

        Args:
            error: The original exception that occurred.
            operation: The operation being performed ('create' or 'update').

        Raises:
            ResourceCreationError: For create operations with validation errors.
            UnprocessableEntityError: For update operations with validation errors.
        """
        error_msg = str(error)
        if "admin" in error_msg.lower() or "permission" in error_msg.lower():
            error_class = (
                ResourceCreationError
                if operation == "create"
                else UnprocessableEntityError
            )
            raise error_class(
                f"Cannot {operation} user group: {error_msg}. "
                "Note: Users with admin organization roles cannot be added to UserGroups. "
                "Only users with project-based roles (org role 'None') can be added."
            ) from error
        else:
            error_class = (
                ResourceCreationError
                if operation == "create"
                else UnprocessableEntityError
            )
            raise error_class(
                f"Cannot {operation} user group: {error_msg}"
            ) from error

    def _get_projects_set(
        self, project_nodes: List[Dict[str, Any]]
    ) -> Set[Project]:
        """Convert project nodes from GraphQL response to Project objects.

        Args:
            project_nodes: List of project dictionaries from GraphQL response.

        Returns:
            Set of Project objects.
        """
        projects = set()
        for node in project_nodes:
            project_values: defaultdict[str, Any] = defaultdict(lambda: None)
            project_values["id"] = node["id"]
            project_values["name"] = node["name"]
            # Provide default values for required fields
            project_values["mediaType"] = MediaType.Image.value
            project_values["editorTaskType"] = EditorTaskType.Missing.value
            projects.add(Project(self.client, project_values))
        return projects

    def _get_members_set(
        self, members_data: Dict[str, Any]
    ) -> Set[UserGroupMember]:
        """Convert member data from GraphQL response to UserGroupMember objects.

        Uses the userGroupRoles from the GraphQL response to create UserGroupMember
        objects with the correct roles.

        Args:
            members_data: Dictionary containing member nodes from GraphQL response.

        Returns:
            Set of UserGroupMember objects with their UserGroup roles.
        """
        members = set()
        member_nodes = members_data.get("nodes", [])
        user_group_roles = members_data.get("userGroupRoles", [])

        # Get all roles to map IDs to names
        from labelbox.schema.role import get_roles

        all_roles = get_roles(self.client)
        role_id_to_role = {role.uid: role for role in all_roles.values()}

        # Create a mapping from userId to roleId
        user_role_mapping = {
            role_data["userId"]: role_data["roleId"]
            for role_data in user_group_roles
        }

        for node in member_nodes:
            # Create User with minimal required fields
            user_values: defaultdict[str, Any] = defaultdict(lambda: None)
            user_values["id"] = node["id"]
            user_values["email"] = node["email"]
            user = User(self.client, user_values)

            # Get the role for this user from the mapping
            role_id = user_role_mapping.get(node["id"])
            if role_id and role_id in role_id_to_role:
                # Use the actual Role object with proper name resolution
                role = role_id_to_role[role_id]
                members.add(UserGroupMember(user=user, role=role))

        return members
