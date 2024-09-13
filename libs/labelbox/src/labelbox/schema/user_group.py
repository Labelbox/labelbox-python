from enum import Enum
from typing import Set, Iterator
from collections import defaultdict

from labelbox import Client
from labelbox.exceptions import ResourceCreationError
from labelbox.schema.user import User
from labelbox.schema.project import Project
from labelbox.exceptions import (
    UnprocessableEntityError,
    MalformedQueryException,
    ResourceNotFoundError,
)
from labelbox.schema.queue_mode import QueueMode
from labelbox.schema.ontology_kind import EditorTaskType
from labelbox.schema.media_type import MediaType
from pydantic import BaseModel, ConfigDict


class UserGroupColor(Enum):
    """
    Enum representing the colors available for a group.

    Attributes:
        BLUE (str): Hex color code for blue (#9EC5FF).
        PURPLE (str): Hex color code for purple (#CEB8FF).
        ORANGE (str): Hex color code for orange (#FFB35F).
        CYAN (str): Hex color code for cyan (#4ED2F9).
        PINK (str): Hex color code for pink (#FFAEA9).
        LIGHT_PINK (str): Hex color code for light pink (#FFA9D5).
        GREEN (str): Hex color code for green (#3FDC9A).
        YELLOW (str): Hex color code for yellow (#E7BF00).
        GRAY (str): Hex color code for gray (#B8C4D3).
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
    """
    Represents a user group in Labelbox.

    Attributes:
        id (str): The ID of the user group.
        name (str): The name of the user group.
        color (UserGroupColor): The color of the user group.
        users (Set[UserGroupUser]): The set of users in the user group.
        projects (Set[UserGroupProject]): The set of projects associated with the user group.
        client (Client): The Labelbox client object.

    Methods:
        __init__(self, client: Client)
        get(self) -> "UserGroup"
        update(self) -> "UserGroup"
        create(self) -> "UserGroup"
        delete(self) -> bool
        get_user_groups(client: Client) -> Iterator["UserGroup"]
    """

    id: str
    name: str
    color: UserGroupColor
    users: Set[User]
    projects: Set[Project]
    client: Client
    model_config = ConfigDict(arbitrary_types_allowed=True)

    def __init__(
        self,
        client: Client,
        id: str = "",
        name: str = "",
        color: UserGroupColor = UserGroupColor.BLUE,
        users: Set[User] = set(),
        projects: Set[Project] = set(),
    ):
        """
        Initializes a UserGroup object.

        Args:
            client (Client): The Labelbox client object.
            id (str, optional): The ID of the user group. Defaults to an empty string.
            name (str, optional): The name of the user group. Defaults to an empty string.
            color (UserGroupColor, optional): The color of the user group. Defaults to UserGroupColor.BLUE.
            users (Set[User], optional): The set of users in the user group. Defaults to an empty set.
            projects (Set[Project], optional): The set of projects associated with the user group. Defaults to an empty set.

        Raises:
            RuntimeError: If the experimental feature is not enabled in the client.
        """
        super().__init__(
            client=client,
            id=id,
            name=name,
            color=color,
            users=users,
            projects=projects,
        )
        if not self.client.enable_experimental:
            raise RuntimeError(
                "Please enable experimental in client to use UserGroups"
            )

    def get(self) -> "UserGroup":
        """
        Reloads the user group information from the server.

        This method sends a GraphQL query to the server to fetch the latest information
        about the user group, including its name, color, projects, and members. The fetched
        information is then used to update the corresponding attributes of the `Group` object.

        Returns:
            UserGroup: The updated `UserGroup` object.

        Raises:
            ResourceNotFoundError: If the query fails to fetch the group information.
            ValueError: If the group ID is not provided.
        """
        if not self.id:
            raise ValueError("Group id is required")
        query = """
            query GetUserGroupPyApi($id: ID!) {
                userGroup(where: {id: $id}) {
                    id
                    name
                    color
                    projects {
                        nodes {
                            id
                            name
                        }
                        totalCount
                    }
                    members {
                        nodes {
                            id
                            email
                        }
                        totalCount
                    }
                }
            }        
        """
        params = {
            "id": self.id,
        }
        result = self.client.execute(query, params)
        if not result:
            raise ResourceNotFoundError(
                message="Failed to get user group as user group does not exist"
            )
        self.name = result["userGroup"]["name"]
        self.color = UserGroupColor(result["userGroup"]["color"])
        self.projects = self._get_projects_set(
            result["userGroup"]["projects"]["nodes"]
        )
        self.users = self._get_users_set(
            result["userGroup"]["members"]["nodes"]
        )
        return self

    def update(self) -> "UserGroup":
        """
        Updates the group in Labelbox.

        Returns:
            UserGroup: The updated UserGroup object. (self)

        Raises:
            ResourceNotFoundError: If the update fails due to unknown user group
            UnprocessableEntityError: If the update fails due to a malformed input
            ValueError: If the group id or name is not provided
        """
        if not self.id:
            raise ValueError("Group id is required")
        if not self.name:
            raise ValueError("Group name is required")
        query = """
        mutation UpdateUserGroupPyApi($id: ID!, $name: String!, $color: String!, $projectIds: [String!]!, $userIds: [String!]!) {
            updateUserGroup(
                where: {id: $id}
                data: {name: $name, color: $color, projectIds: $projectIds, userIds: $userIds}
            ) {
                group {
                    id
                    name
                    color
                    projects {
                        nodes {
                            id
                            name
                        }
                    }
                    members {
                        nodes {
                            id
                            email
                        }
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
            "userIds": [user.uid for user in self.users],
        }
        try:
            result = self.client.execute(query, params)
            if not result:
                raise ResourceNotFoundError(
                    message="Failed to update user group as user group does not exist"
                )
        except MalformedQueryException as e:
            raise UnprocessableEntityError("Failed to update user group") from e
        return self

    def create(self) -> "UserGroup":
        """
        Creates a new user group.

        Raises:
            ResourceCreationError: If the group already exists.
            ValueError: If the group name is not provided.

        Returns:
            UserGroup: The created user group.
        """
        if self.id:
            raise ResourceCreationError("Group already exists")
        if not self.name:
            raise ValueError("Group name is required")
        query = """
        mutation CreateUserGroupPyApi($name: String!, $color: String!, $projectIds: [String!]!, $userIds: [String!]!) {
            createUserGroup(
                data: {
                    name: $name,
                    color: $color,
                    projectIds: $projectIds,
                    userIds: $userIds
                }
            ) {
                group {
                    id
                    name
                    color
                    projects {
                        nodes {
                            id
                            name
                        }
                    }
                    members {
                        nodes {
                            id
                            email
                        }
                    }
                }
            }
        }
        """
        params = {
            "name": self.name,
            "color": self.color.value,
            "projectIds": [project.uid for project in self.projects],
            "userIds": [user.uid for user in self.users],
        }
        result = None
        error = None
        try:
            result = self.client.execute(query, params)
        except Exception as e:
            error = e
        if not result or error:
            # this is client side only, server doesn't have an equivalent error
            raise ResourceCreationError(
                f"Failed to create user group, either user group name is in use currently, or provided user or projects don't exist server error: {error}"
            )
        result = result["createUserGroup"]["group"]
        self.id = result["id"]
        return self

    def delete(self) -> bool:
        """
        Deletes the user group from Labelbox.

        This method sends a mutation request to the Labelbox API to delete the user group
        with the specified ID. If the deletion is successful, it returns True. Otherwise,
        it raises an UnprocessableEntityError and returns False.

        Returns:
            bool: True if the user group was successfully deleted, False otherwise.

        Raises:
            ResourceNotFoundError: If the deletion of the user group fails due to not existing
            ValueError: If the group ID is not provided.
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
        params = {"id": self.id}
        result = self.client.execute(query, params)
        if not result:
            raise ResourceNotFoundError(
                message="Failed to delete user group as user group does not exist"
            )
        return result["deleteUserGroup"]["success"]

    def get_user_groups(self) -> Iterator["UserGroup"]:
        """
        Gets all user groups in Labelbox.

        Args:
            client (Client): The Labelbox client.

        Returns:
            Iterator[UserGroup]: An iterator over the user groups.
        """
        query = """
            query GetUserGroupsPyApi($after: String) {
                userGroups(after: $after) {
                    nodes {
                        id
                        name
                        color
                        projects {
                            nodes {
                                id
                                name
                            }
                            totalCount
                        }
                        members {
                            nodes {
                                id
                                email
                            }
                            totalCount
                        }
                    }
                    nextCursor
                }
            }
        """
        nextCursor = None
        while True:
            userGroups = self.client.execute(query, {"after": nextCursor})[
                "userGroups"
            ]
            if not userGroups:
                return
                yield
            groups = userGroups["nodes"]
            for group in groups:
                userGroup = UserGroup(self.client)
                userGroup.id = group["id"]
                userGroup.name = group["name"]
                userGroup.color = UserGroupColor(group["color"])
                userGroup.users = self._get_users_set(group["members"]["nodes"])
                userGroup.projects = self._get_projects_set(
                    group["projects"]["nodes"]
                )
                yield userGroup
            nextCursor = userGroups["nextCursor"]
            if not nextCursor:
                return
                yield

    def _get_users_set(self, user_nodes):
        """
        Retrieves a set of User objects from the given user nodes.

        Args:
            user_nodes (list): A list of user nodes containing user information.

        Returns:
            set: A set of User objects.
        """
        users = set()
        for user in user_nodes:
            user_values = defaultdict(lambda: None)
            user_values["id"] = user["id"]
            user_values["email"] = user["email"]
            users.add(User(self.client, user_values))
        return users

    def _get_projects_set(self, project_nodes):
        """
        Retrieves a set of projects based on the given project nodes.

        Args:
            project_nodes (list): A list of project nodes.

        Returns:
            set: A set of Project objects.
        """
        projects = set()
        for project in project_nodes:
            project_values = defaultdict(lambda: None)
            project_values["id"] = project["id"]
            project_values["name"] = project["name"]
            project_values["queueMode"] = QueueMode.Batch.value
            project_values["editorTaskType"] = EditorTaskType.Missing.value
            project_values["mediaType"] = MediaType.Image.value
            projects.add(Project(self.client, project_values))
        return projects
