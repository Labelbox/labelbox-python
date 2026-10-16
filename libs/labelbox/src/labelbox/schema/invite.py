from typing import TYPE_CHECKING, Optional, Union
from dataclasses import dataclass
from enum import Enum

from labelbox.orm.db_object import DbObject
from labelbox.orm.model import Field
from labelbox.schema.role import ProjectRole, format_role

from labelbox.pagination import PaginatedCollection

if TYPE_CHECKING:
    from labelbox import Client


@dataclass
class InviteLimit:
    """
    remaining (int): Number of invites remaining in the org
    used (int): Number of invites used in the org
    limit (int): Maximum number of invites available to the org
    """

    remaining: int
    used: int
    limit: int


class InviteMemberStatus(str, Enum):
    """Outcome of one address in `Organization.invite_users`."""

    INVITED = "INVITED"
    ADDED = "ADDED"
    ALREADY_MEMBER = "ALREADY_MEMBER"
    ALREADY_INVITED = "ALREADY_INVITED"
    INVALID_EMAIL = "INVALID_EMAIL"
    DUPLICATE = "DUPLICATE"
    SEAT_LIMIT = "SEAT_LIMIT"
    NOT_ALLOWED = "NOT_ALLOWED"
    FAILED = "FAILED"


@dataclass
class InviteResult:
    """
    email (str): The address as the server checked it: trimmed and lowercased when valid, trimmed when invalid
    status (InviteMemberStatus | str): The outcome; an unknown future value stays a string
    reason (Optional[str]): Why the address is not allowed or already a member, for example `GROUP_ACCESS`
    invite_id (Optional[str]): The invite id when an invite was created
    """

    email: str
    status: Union[InviteMemberStatus, str]
    reason: Optional[str]
    invite_id: Optional[str]


class Invite(DbObject):
    """
    An object representing a user invite
    """

    created_at = Field.DateTime("created_at")
    organization_role_name = Field.String("organization_role_name")
    email = Field.String("email", "inviteeEmail")

    def __init__(self, client, invite_response):
        project_roles = invite_response.pop("projectInvites", [])
        super().__init__(client, invite_response)

        self.project_roles = []

        # If a project is deleted then it doesn't show up in the invite
        for pr in project_roles:
            try:
                project = client.get_project(pr["projectId"])
                if project:  # Check if project exists
                    self.project_roles.append(
                        ProjectRole(
                            project=project,
                            role=client.get_roles()[
                                format_role(pr["projectRoleName"])
                            ],
                        )
                    )
            except Exception:
                # Skip this project role if the project is no longer available
                continue

    def cancel(self) -> bool:
        """
        Cancels this invite.

        This will prevent the invited user from accepting the invitation.

        Returns:
            bool: True if the invite was successfully canceled, False otherwise.
        """

        # Case of a newly invited user
        if self.uid == "invited":
            return False

        query_str = """
            mutation CancelInvitePyApi($where: WhereUniqueIdInput!) {
                cancelInvite(where: $where) {
                    id
                }
            }"""
        result = self.client.execute(
            query_str, {"where": {"id": self.uid}}, experimental=True
        )
        return (
            result is not None
            and "cancelInvite" in result
            and result.get("cancelInvite") is not None
        )

    @staticmethod
    def get_project_invites(
        client: "Client", project_id: str
    ) -> PaginatedCollection:
        """
        Retrieves all invites for a specific project.

        Args:
            client (Client): The Labelbox client instance.
            project_id (str): The ID of the project to get invites for.

        Returns:
            PaginatedCollection: A collection of Invite objects for the specified project.
        """
        query = """query GetProjectInvitationsPyApi(
                    $from: ID
                    $first: PageSize
                    $projectId: ID!
                    ) {
                    project(where: { id: $projectId }) {
                        id
                        invites(from: $from, first: $first) {
                        nodes {
                            id
                            createdAt
                            organizationRoleName
                            inviteeEmail
                            projectInvites {
                            id
                            projectRoleName
                            projectId
                            }
                        }
                        nextCursor
                        }
                    }
                    }"""

        invites = PaginatedCollection(
            client,
            query,
            {"projectId": project_id, "search": ""},
            ["project", "invites", "nodes"],
            Invite,
            cursor_path=["project", "invites", "nextCursor"],
        )
        return invites

    @staticmethod
    def get_invites(client: "Client") -> PaginatedCollection:
        """
        Retrieves all invites for the organization.

        Args:
            client (Client): The Labelbox client instance.

        Returns:
            PaginatedCollection: A collection of Invite objects for the organization.
        """
        query_str = """query GetOrgInvitationsPyApi($from: ID, $first: PageSize) {
            organization {
                id
                invites(from: $from, first: $first) {
                nodes {
                    id
                    createdAt
                    organizationRoleName
                    inviteeEmail
                    projectInvites {
                    id
                    projectRoleName
                    projectId
                    }
                }
                nextCursor
                }
            }
            }"""
        invites = PaginatedCollection(
            client,
            query_str,
            {},
            ["organization", "invites", "nodes"],
            Invite,
            cursor_path=["organization", "invites", "nextCursor"],
        )
        return invites
