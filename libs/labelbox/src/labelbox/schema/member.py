from typing import Optional
from labelbox.exceptions import (
    MalformedQueryException,
    ResourceNotFoundError,
    UnprocessableEntityError,
)
from typing import Set, Iterator, Any
from pydantic import (
    Field,
    field_validator,
    model_serializer,
    model_validator,
)
from labelbox.utils import _CamelCaseMixin
from labelbox.schema.role import Role
from labelbox import Client


class ProjectMembership(_CamelCaseMixin):
    """Represents a members project role

    Args:
        project_id (str): id of the project you want the member included
        role (Optional[Role]): Members role for the project. None represents the member having a default role.
    """

    project_id: str
    role: Optional[Role] = None

    def __hash__(self) -> int:
        return self.project_id.__hash__()

    @model_serializer()
    def serialize_model(self):
        return {
            "projectId": self.project_id,
            "roleId": None if self.role is None else self.role.id,
        }


class Member(_CamelCaseMixin):
    """
    Represents a member in Labelbox.

    Attributes:
        id (str, frozen): The ID of the member. Defaults to current users id.
        updated_at (str, frozen): Last time member was updated.
        created_at (str, frozen): When member was created.
        email (str, frozen): Email of member.
        name (str, frozen): Name of the member.
        nickname (str, frozen): Nickname of the member.
        picture (str, frozen): Picture of the member.
        is_viewer (bool, frozen): Indicates if member is a viewer of org.
        is_external_user (bool, frozen): Indicates if member is a external user of org
        accessible_project_count (int, frozen): Them amount of projects the user can access
        project_memberships (Set[ProjectMembership]): The current projects with role the user has access towards
        can_access_all_projects (bool): If member can access all projects inside org.
        default_role (Optional[Role]): Shows the members default role. None means the member does not have a default role.
        user_group_ids (Set[str]): The user group ids the member is associated with.
        client (Client): The Labelbox client object

    Methods:
        get(self) -> "Member"
        update(self) -> "Member"
        delete(self) -> bool
        get_user_groups(self, search: str, roles: Optional[list[Role]], group_ids: Optional[list[str]]) -> Iterator["Member"]

    Raises:
        RuntimeError: If the experimental feature is not enabled in the client.
    """

    id: str = Field(frozen=True)
    updated_at: str = Field(default="", frozen=True)
    created_at: str = Field(default="", frozen=True)
    email: str = Field(default="", frozen=True)
    name: Optional[str] = Field(default=None, frozen=True)
    nickname: Optional[str] = Field(default=None, frozen=True)
    picture: Optional[str] = Field(default=None, frozen=True)
    is_viewer: bool = Field(default=False, frozen=True)
    is_external_user: bool = Field(default=False, frozen=True)
    accessible_project_count: Optional[int] = Field(default=None, frozen=True)
    project_memberships: Set[ProjectMembership] = Field(default=set())
    can_access_all_projects: bool = Field(default=False)
    default_role: Optional[Role] = Field(default=None)
    user_group_ids: Set[str] = Field(default=set())
    client: Client
    _current_user_id: str

    def __init__(self, **data):
        """set private attribute"""
        super().__init__(**data)
        self._current_user_id = self.client.get_user().uid

    @field_validator("client", mode="before")
    @classmethod
    def experimental(cls, v: Client):
        if not v.enable_experimental:
            raise RuntimeError(
                "Please enable experimental in client to use Members"
            )
        return v

    @model_validator(mode="before")
    def current_user(data: Any) -> Any:
        if "id" not in data:
            data["id"] = data["client"].get_user().uid
        return data

    def get(self) -> "Member":
        """
        Reloads the members information from the server.

        This method sends a GraphQL query to the server to fetch the latest information
        about the members, The fetched
        information is then used to update the corresponding attributes of the `Member` object.

        Returns:
            Member: The updated `Member` object.

        Raises:
            ResourceNotFoundError: If the query fails to fetch the member information.
        """

        if not self.id:
            raise ValueError("Id is required")
        query = """
            query GetMemberReworkPyApi($userId: ID!) {
                user(where: { id: $userId }) {
                id
                updatedAt
                createdAt
                name
                nickname
                email
                defaultRole {
                    id
                    name
                }
                picture
                isViewer
                isExternalUser
                canAccessAllProjects
                accessibleProjectCount
                userGroups {
                    nodes {
                        id
                    }
                }
                __typename
                }
                projectMemberships(userId: $userId) {
                    role {
                        id
                        name
                    }
                    project {
                        id
                    }
                }
            }
        """
        params = {"userId": self.id}

        result = self.client.execute(query, params, experimental=True)
        if not result:
            raise ResourceNotFoundError(
                message="Failed to find user as user does not exist"
            )

        user = {
            **result["user"],
            "client": self.client,
            "userGroups": [],
            "projectMemberships": [],
            "defaultRole": None,
        }
        model = self.model_copy(update=Member(**user).model_dump())

        for userGroup in result["user"]["userGroups"]["nodes"]:
            model.user_group_ids.add(userGroup["id"])

        model.default_role = Role(
            self.client,
            field_values={
                "id": result["user"]["defaultRole"]["id"],
                "name": result["user"]["defaultRole"]["name"],
            },
        )

        for project_membership in result["projectMemberships"]:
            project_membership["role"] = Role(
                self.client,
                field_values={
                    "id": project_membership["role"]["id"],
                    "name": project_membership["role"]["name"],
                },
            )
            project_membership["projectId"] = project_membership["project"][
                "id"
            ]
            model.project_memberships.add(
                ProjectMembership(**project_membership)
            )

        return model

    def update(self) -> "Member":
        """
        Updates the member in Labelbox.

        Returns:
            Member: The updated Member object. (self)

        Raises:
            ResourceNotFoundError: If the update fails due to unknown member
            UnprocessableEntityError: If the update fails due to a malformed input
        """
        query = """
            mutation SetUserAccessPyApi($id: ID!, $roleId: ID!, $canAccessAllProjects: Boolean!, $groupIds: [String!], $projectMemberships: [ProjectMembershipsInput!]) {
            setUserAccess(
                where: {id: $id}
                data: {roleId: $roleId, canAccessAllProjects: $canAccessAllProjects, groupIds: $groupIds, projectMemberships: $projectMemberships}
            ) {
                id
                __typename
            }
            }
        """
        params = {
            "id": self.id,
            "roleId": self.default_role.uid if self.default_role else None,
            "canAccessAllProjects": self.can_access_all_projects,
            "groupIds": self.user_group_ids,
            "projectMemberships": [
                project_membership.model_dump()
                for project_membership in self.project_memberships
            ],
        }

        try:
            result = self.client.execute(query, params, experimental=True)
            if not result:
                raise ResourceNotFoundError(
                    message="Failed to update member as member does not exist"
                )
        except MalformedQueryException as e:
            raise UnprocessableEntityError("Failed to update member") from e
        return self

    def delete(self) -> bool:
        """
        Deletes the member from Labelbox.

        This method sends a mutation request to the Labelbox API to delete the member
        with the specified ID. If the deletion is successful, it returns True. Otherwise,
        it raises an UnprocessableEntityError and returns False.

        Returns:
            bool: True if the member was successfully deleted, False otherwise.

        Raises:
            ResourceNotFoundError: If the deletion of the member fails due to not existing
            ValueError: If the member id is current member id.
        """

        query = """
            mutation DeleteMemberPyApi($id: ID!) {
                updateUser(where: { id: $id }, data: { deleted: true }) {
                    id
                    deleted
                }
            }
            """

        if self.id == self._current_user_id:
            raise ValueError("Unable to delete self")

        params = {"id": self.id}

        result = self.client.execute(query, params, experimental=True)
        if not result:
            raise ResourceNotFoundError(
                message="Failed to delete member as member does not exist"
            )
        return result["data"]["updateUser"]["deleted"]

    def _get_project_memberships(self, user_id: str) -> Set[ProjectMembership]:
        """
        Retrieves a set of project membership objects from the given user_id.

        Args:
            user_id (str): User id you are getting project memberships on.

        Returns:
            set: A set of project memberships.
        """
        query = """
            query GetMemberReworkPyApi($userId: ID!) {
                projectMemberships(userId: $userId) {
                    role {
                        id
                        name
                    }
                    project {
                        id
                    }
                }
            }
            """

        params = {"userId": user_id}
        result = self.client.execute(query, params)

        project_memberships = set()
        for project_membership in result["projectMemberships"]:
            project_membership["role"] = Role(
                self.client,
                field_values={
                    "id": project_membership["role"]["id"],
                    "name": project_membership["role"]["name"],
                },
            )
            project_membership["projectId"] = project_membership["project"][
                "id"
            ]

            project_memberships.add(ProjectMembership(**project_membership))

        return project_memberships

    def get_members(
        self,
        search: str = "",
        roles: Optional[list[Role]] = None,
        group_ids: Optional[list[str]] = None,
    ) -> Iterator["Member"]:
        """
        Gets all members in Labelbox.

        Args:
            search (str): Email of user you are looking to receive.
            roles (Optional[list[Role]]): Role of the users you are wanting to receive.
            group_ids (Optional[list[str]]): List of user group ids.

        Returns:
            Iterator[UserGroup]: An iterator over the user groups.
        """
        query = """
            query GetOrganizationMembersPyApi(
                $first: PageSize!
                $skip: Int
                $search: String
                $roleIds: [String!]
                $groupIds: [String!]
                $complexFilters: [ComplexFilter!]
                ) {
                    users(
                        where: {
                        email_contains: $search
                        organizationRoleId_in: $roleIds
                        groupId_in: $groupIds
                        complexFilters: $complexFilters
                        }
                        first: $first
                        skip: $skip
                    ) {
                        id
                        updatedAt
                        createdAt
                        name
                        nickname
                        email
                        defaultRole {
                            id
                            name
                        }
                        picture
                        isViewer
                        isExternalUser
                        canAccessAllProjects
                        accessibleProjectCount
                        userGroups {
                            nodes {
                                id
                            }
                        }
                    }
                }
            """
        previous_batch = 0
        batch_size = 100
        while True:
            params = {
                "first": batch_size,
                "skip": previous_batch,
                "search": search,
                "roleIds": [role.uid for role in roles] if roles else None,
                "groupIds": group_ids,
                "complexFilters": None,
            }
            members = self.client.execute(query, params, experimental=True)[
                "users"
            ]

            if not members:
                return
                yield

            for member in members:
                member["projectMemberships"] = self._get_project_memberships(
                    member["id"]
                )
                user_groups = set()

                for user_group in member["userGroups"]["nodes"]:
                    user_groups.add(user_group["id"])
                member["userGroupIds"] = user_groups

                member["defaultRole"] = Role(
                    self.client,
                    field_values={
                        "id": member["defaultRole"]["id"],
                        "name": member["defaultRole"]["name"],
                    },
                )

                yield Member(client=self.client, **member)

            previous_batch += batch_size
