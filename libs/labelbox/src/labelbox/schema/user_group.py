from enum import Enum
from typing import Set, List, Optional, Union, TypedDict, Iterator

from labelbox import Client
from labelbox.exceptions import ResourceCreationError
from labelbox.pydantic_compat import BaseModel
from labelbox.schema.user import User
from labelbox.schema.project import Project


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


class UserGroupUser(BaseModel):
    """
    Represents a user in a group.

    Attributes:
        id (str): The ID of the user.
        email (str): The email of the user.
    """
    id: str
    email: str

    def __hash__(self):
        return hash((self.id))

    def __eq__(self, other):
        if not isinstance(other, UserGroupUser):
            return False
        return self.id == other.id


class UserGroupProject(BaseModel):
    """
    Represents a project in a group.

    Attributes:
        id (str): The ID of the project.
        name (str): The name of the project.
    """
    id: str
    name: str

    def __hash__(self):
        return hash((self.id))

    def __eq__(self, other):
        """
        Check if this GroupProject object is equal to another GroupProject object.

        Args:
            other (GroupProject): The other GroupProject object to compare with.

        Returns:
            bool: True if the two GroupProject objects are equal, False otherwise.
        """
        if not isinstance(other, UserGroupProject):
            return False
        return self.id == other.id


class UserGroupParameters(TypedDict):
    """
    Represents the parameters for a user group.

    Attributes:
        id (Optional[str]): The ID of the user group.
        name (Optional[str]): The name of the user group.
        color (Optional[UserGroupColor]): The color of the user group.
        users (Optional[Set[Union[UserGroupUser, User]]]): The users in the user group.
        projects (Optional[Set[Union[UserGroupProject, Project]]]): The projects associated with the user group.
    """
    id: Optional[str]
    name: Optional[str]
    color: Optional[UserGroupColor]
    users: Optional[Set[Union[UserGroupUser, User]]]
    projects: Optional[Set[Union[UserGroupProject, Project]]]


class UserGroup:
    """
    Represents a user group in Labelbox.

    Args:
        client (Client): The Labelbox client.
        **kwargs: Additional keyword arguments for initializing the UserGroup object.

    Attributes:
        _id (str): The ID of the user group.
        _name (str): The name of the user group.
        _color (UserGroupColor): The color of the user group.
        _users (Set[Union[UserGroupUser, User]]): The set of user IDs in the user group.
        _projects (Set[Union[UserGroupProject, Project]]): The set of project IDs in the user group.
        _client (Client): The Labelbox client.
    """
    _id: str = None
    _name: str = None
    _color: UserGroupColor = None
    _users: Set[Union[UserGroupUser, User]] = None
    _projects: Set[Union[UserGroupProject, Project]] = None
    _client: Client

    def __init__(self,
                 client: Client,
                 reload=True,
                 **kwargs: UserGroupParameters):
        """
        Initializes a Group object.

        Args:
            client (Client): The Labelbox client.
            **kwargs: Additional keyword arguments for initializing the Group object.
        """
        super().__init__()
        self.color = kwargs.get('color', UserGroupColor.BLUE)
        self.users = kwargs.get('users', set())
        self.projects = kwargs.get('projects', set())
        self.client = client

        # runs against _gql
        if not client.enable_experimental:
            raise RuntimeError(
                "Experimental features are not enabled. Please enable them in the client to use this feature."
            )

        self.name = kwargs.get('name', None)
        self.id = kwargs.get('id', None)
        # partial respentation of the group, reload
        if self.id is not None and reload:
            self._reload()

    def _reload(self):
        """
        Reloads the user group information from the server.

        This method sends a GraphQL query to the server to fetch the latest information
        about the user group, including its name, color, projects, and members. The fetched
        information is then used to update the corresponding attributes of the `Group` object.

        Returns:
            None
        """
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
        self.name = result["userGroup"]["name"]
        self.color = UserGroupColor(result["userGroup"]["color"])
        self.projects = {
            UserGroupProject(id=project["id"], name=project["name"])
            for project in result["userGroup"]["projects"]["nodes"]
        }
        self.users = {
            UserGroupUser(id=member["id"], email=member["email"])
            for member in result["userGroup"]["members"]["nodes"]
        }

    @property
    def id(self) -> str:
        """
        Gets the ID of the group.

        Returns:
            str: The ID of the group.
        """
        return self._id

    @id.setter
    def id(self, value: str) -> None:
        """
        Sets the ID of the group.

        Args:
            value (str): The ID to set.
        """
        self._id = value

    @property
    def name(self) -> str:
        """
        Gets the name of the group.

        Returns:
            str: The name of the group.
        """
        return self._name

    @name.setter
    def name(self, value: str) -> None:
        """
        Sets the name of the group.

        Args:
            value (str): The name to set.
        """
        self._name = value

    @property
    def color(self) -> UserGroupColor:
        """
        Gets the color of the group.

        Returns:
            GroupColor: The color of the group.
        """
        return self._color

    @color.setter
    def color(self, value: UserGroupColor) -> None:
        """
        Sets the color of the group.

        Args:
            value (GroupColor): The color to set.
        """
        self._color = value

    @property
    def users(self) -> Set[Union[UserGroupUser, User]]:
        """
        Gets the list of user IDs in the group.

        Returns:
            Set[GroupUser]: The list of user IDs in the group.
        """
        return self._users

    @users.setter
    def users(self, value: Set[Union[UserGroupUser, User]]) -> None:
        """
        Sets the list of user IDs in the group.

        Args:
            value (Set[GroupUser]): The list of user IDs to set.
        """
        self._users = value

    @property
    def projects(self) -> Set[UserGroupProject]:
        """
        Gets the list of project IDs in the group.

        Returns:
            Set[GroupProject]: The list of project IDs in the group.
        """
        return self._projects

    @projects.setter
    def projects(self, value: Set[UserGroupProject]) -> None:
        """
        Sets the list of project IDs in the group.

        Args:
            value (Set[GroupProject]): The list of project IDs to set.
        """
        self._projects = value

    def update(self) -> "UserGroup":
        """
        Updates the group in Labelbox.
        """
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
            "id":
                self.id,
            "name":
                self.name,
            "color":
                self.color.value,
            "projectIds": [
                project.id if hasattr(project, 'id') else project.uid
                for project in self.projects
            ],
            "userIds": [
                user.id if hasattr(user, 'id') else user.uid
                for user in self.users
            ]
        }
        self.client.execute(query, params)
        return self

    def create(self) -> "UserGroup":
        """
        Creates a new group in Labelbox.

        Args:
            client (Client): The Labelbox client.
            name (str): The name of the group.
            color (GroupColor, optional): The color of the group. Defaults to GroupColor.BLUE.
            users (List[User], optional): The users to add to the group. Defaults to [].
            projects (List[Project], optional): The projects to add to the group. Defaults to [].

        Returns:
            Group: The newly created group.
        """
        if self.id is not None:
            raise ResourceCreationError("Group already exists")
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
            "name":
                self.name,
            "color":
                self.color.value,
            "projectIds": [
                project.id if hasattr(project, 'id') else project.uid
                for project in self.projects
            ],
            "userIds": [
                user.id if hasattr(user, 'id') else user.uid
                for user in self.users
            ]
        }
        result = self.client.execute(query, params)["createUserGroup"]["group"]
        self.id = result["id"]
        return self

    def delete(self) -> bool:
        """
        Deletes the group from Labelbox.

        Returns:
            bool: True if the group was successfully deleted, False otherwise.
        """
        query = """
        mutation DeleteUserGroupPyApi($id: ID!) {
            deleteUserGroup(where: {id: $id}) {
                success
            }
        }
        """
        params = {"id": self.id}
        result = self.client.execute(query, params)
        return result["deleteUserGroup"]["success"]

    @staticmethod
    def get_user_groups(client: Client) -> Iterator["UserGroup"]:
        """
        Gets all groups in Labelbox.

        Args:
            client (Client): The Labelbox client.

        Returns:
            List[Group]: The list of groups.
        """
        query = """
            query GetUserGroupsPyApi {
                userGroups {
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
            userGroups = client.execute(
                query, {"nextCursor": nextCursor})["userGroups"]
            groups = userGroups["nodes"]
            for group in groups:
                yield UserGroup(client,
                                reload=False,
                                id=group["id"],
                                name=group["name"],
                                color=UserGroupColor(group["color"]),
                                users={
                                    UserGroupUser(id=member["id"],
                                                  email=member["email"])
                                    for member in group["members"]["nodes"]
                                },
                                projects={
                                    UserGroupProject(id=project["id"],
                                                     name=project["name"])
                                    for project in group["projects"]["nodes"]
                                })
            nextCursor = userGroups["nextCursor"]
            # this doesn't seem to be implemented right now to return a value other than null from the api
            if nextCursor:
                break
