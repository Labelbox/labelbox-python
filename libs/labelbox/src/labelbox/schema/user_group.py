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
    and collaboration. This implementation provides enhanced validation and
    member management capabilities.

    Attributes:
        id: Unique identifier for the user group.
        name: Display name of the user group.
        color: Visual color identifier for the group.
        description: Optional description of the group's purpose.
        notify_members: Whether to notify members of group changes.
        default_role: Default role assigned to users added via the legacy users field.
        users: Legacy set of users (maintained for backward compatibility).
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
    default_role: Optional[Role] = None
    users: Set[User] = Field(default_factory=set)
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
        default_role: Optional[Role] = None,
        users: Optional[Set[User]] = None,
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
            default_role: Default role for users added via legacy users field.
            users: Legacy set of users for backward compatibility.
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
            default_role=default_role,
            users=users or set(),
            members=members or set(),
            projects=projects or set(),
        )

    def model_post_init(self, __context: Any) -> None:
        """Set default_role to LABELER if not specified.

        Args:
            __context: Pydantic context (unused).
        """
        if self.default_role is None:
            try:
                roles = self.client.get_roles()
                self.default_role = roles.get("LABELER")
            except Exception:
                # Silently fail if roles cannot be retrieved
                pass

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
                userGroup(where: {id: $id}) {
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
                    }
                }
            }
        """

        result = self.client.execute(query, {"id": self.id})
        if not result or not result.get("userGroup"):
            raise ResourceNotFoundError(message="User group not found")

        group_data = result["userGroup"]
        self._update_from_response(group_data)

        return self

    def update(self) -> UserGroup:
        """Update the group in Labelbox.

        Returns:
            Self with updated information from the server.

        Raises:
            ValueError: If group ID or name is not set, or if projects don't exist.
            ResourceNotFoundError: If the group or projects are not found.
            UnprocessableEntityError: If user validation fails.
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

        # Get default role if not set
        if not self.default_role:
            roles = self.client.get_roles()
            self.default_role = roles.get("LABELER")
            if not self.default_role:
                raise ValueError("Unable to get default role for users")

        # Filter eligible users and build user roles
        eligible_users = self._filter_project_based_users()
        user_roles = self._build_user_roles(eligible_users)

        query = """
        mutation UpdateUserGroupPyApi($id: ID!, $name: String!, $color: String!, $projectIds: [ID!]!, $userRoles: [UserRoleInput!], $description: String, $notifyMembers: Boolean) {
            updateUserGroupV3(
                where: { id: $id }
                data: {
                    name: $name
                    color: $color
                    projectIds: $projectIds
                    userRoles: $userRoles
                    description: $description
                    notifyMembers: $notifyMembers
                }
            ) {
                group {
                    id
                    name
                    color
                    description
                    projects { nodes { id name } totalCount }
                    members { 
                        nodes { id email orgRole { id name } } 
                        totalCount 
                    }
                }
            }
        }
        """

        params = {
            "id": self.id,
            "name": self.name,
            "color": self.color.value,
            "projectIds": [project.uid for project in self.projects],
            "userRoles": user_roles,
            "description": self.description,
            "notifyMembers": self.notify_members,
        }

        try:
            result = self.client.execute(query, params, experimental=True)
            if not result:
                raise ResourceNotFoundError("Failed to update user group")

            group_data = result["updateUserGroupV3"]["group"]
            self._update_from_response(group_data)

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
            ResourceCreationError: If creation fails or user validation fails.
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

        # Get default role if not set
        if not self.default_role:
            roles = self.client.get_roles()
            self.default_role = roles.get("LABELER")
            if not self.default_role:
                raise ValueError("Unable to get default role for users")

        # Filter eligible users and build user roles
        eligible_users = self._filter_project_based_users()
        user_roles = self._build_user_roles(eligible_users)

        query = """
        mutation CreateUserGroupPyApi($description: String, $color: String!, $name: String!, $projectIds: [ID!], $userRoles: [UserRoleInput!], $roleId: String, $searchQuery: AlignerrSearchServiceQuery, $notifyMembers: Boolean) {
            createUserGroupV3(
                data: {
                    name: $name
                    description: $description
                    color: $color
                    projectIds: $projectIds
                    userRoles: $userRoles
                    searchQuery: $searchQuery
                    roleId: $roleId
                    notifyMembers: $notifyMembers
                }
            ) {
                group {
                    id
                    name
                    color
                    updatedAt
                    createdByUserName
                    description
                    __typename
                    projects { nodes { id name } totalCount }
                    members { 
                        nodes { id email orgRole { id name } } 
                        totalCount 
                    }
                }
                __typename
            }
        }
        """

        params = {
            "name": self.name,
            "color": self.color.value,
            "projectIds": [project.uid for project in self.projects],
            "userRoles": user_roles,
            "description": self.description,
            "notifyMembers": self.notify_members,
            "roleId": None,
            "searchQuery": None,
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
        self._update_from_response(group_data)

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
    def get_user_groups(client: Client) -> Iterator[UserGroup]:
        """Get all user groups from Labelbox.

        Args:
            client: Labelbox client for API communication.

        Yields:
            UserGroup instances for each group found.
        """
        query = """
            query GetUserGroupsPyApi {
                userGroups {
                    nodes {
                        id
                        name
                        color
                        description
                        projects { nodes { id name } totalCount }
                        members { 
                            nodes { id email orgRole { id name } } 
                            totalCount 
                        }
                    }
                }
            }
        """

        result = client.execute(query)
        if not result or not result.get("userGroups"):
            return

        for group_data in result["userGroups"]["nodes"]:
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

    def _filter_project_based_users(self) -> Set[User]:
        """Filter users to only include users eligible for UserGroups.

        Filters out users with specific admin organization roles that cannot be
        added to UserGroups. Most users should be eligible.

        Returns:
            Set of users that are eligible to be added to the group.
        """
        all_users = set(self.users)
        for member in self.members:
            all_users.add(member.user)

        if not all_users:
            return set()

        user_ids = [user.uid for user in all_users]
        query = """
        query CheckUserOrgRoles($userIds: [ID!]!) {
            users(where: {id_in: $userIds}) {
                id
                orgRole { id name }
            }
        }
        """

        try:
            result = self.client.execute(query, {"userIds": user_ids})
            if not result or "users" not in result:
                return all_users  # Fallback: let server handle validation

            # Check for users with org roles that cannot be used in UserGroups
            # Only users with no org role (project-based users) can be assigned to UserGroups
            eligible_user_ids = set()
            invalid_users = []

            for user_data in result["users"]:
                org_role = user_data.get("orgRole")
                user_id = user_data["id"]
                user_email = user_data.get("email", "unknown")

                if org_role is None:
                    # Users with no org role (project-based users) are eligible
                    eligible_user_ids.add(user_id)
                else:
                    # Users with ANY workspace org role cannot be assigned to UserGroups
                    invalid_users.append(
                        {
                            "id": user_id,
                            "email": user_email,
                            "org_role": org_role.get("name"),
                        }
                    )

            # Raise error if any invalid users found
            if invalid_users:
                error_details = []
                for user in invalid_users:
                    error_details.append(
                        f"User {user['id']} ({user['email']}) has org role '{user['org_role']}'"
                    )

                raise ValueError(
                    f"Cannot create UserGroup with users who have organization roles. "
                    f"Only project-based users (no org role) can be assigned to UserGroups.\n"
                    f"Invalid users:\n"
                    + "\n".join(f"  • {detail}" for detail in error_details)
                )

            return {user for user in all_users if user.uid in eligible_user_ids}

        except Exception:
            return all_users  # Fallback: let server handle validation

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

        # Add legacy users with default role
        for user in self.users:
            if user in eligible_users and self.default_role is not None:
                user_roles.append(
                    {"userId": user.uid, "roleId": self.default_role.uid}
                )

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
        self.users = set()  # Clear legacy users

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

        Since the GraphQL response doesn't include UserGroup role information,
        we preserve the roles that were originally set in the members list.
        This means roles are maintained from creation/update operations.

        Args:
            members_data: Dictionary containing member nodes from GraphQL response.

        Returns:
            Set of UserGroupMember objects with preserved roles.
        """
        members = set()
        member_nodes = members_data.get("nodes", [])

        # Create a mapping of existing members by user ID to preserve roles
        existing_member_roles = {
            member.user.uid: member.role for member in self.members
        }

        for node in member_nodes:
            # Create User with minimal required fields
            user_values: defaultdict[str, Any] = defaultdict(lambda: None)
            user_values["id"] = node["id"]
            user_values["email"] = node["email"]
            user = User(self.client, user_values)

            # Try to preserve the existing role for this user
            user_id = node["id"]
            if user_id in existing_member_roles:
                # Use the preserved role
                role = existing_member_roles[user_id]
                members.add(UserGroupMember(user=user, role=role))
            else:
                # For new members we can't determine the role from the response,
                # use default role if available
                if self.default_role:
                    members.add(
                        UserGroupMember(user=user, role=self.default_role)
                    )

        return members
