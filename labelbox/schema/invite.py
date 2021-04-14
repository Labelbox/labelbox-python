from dataclasses import dataclass

from labelbox.orm.db_object import DbObject, beta
from labelbox.orm.model import Field
from labelbox.schema.role import ProjectRole


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

        self.project_roles = [
            ProjectRole(project=client.get_project(r['projectId']),
                        role=client.get_roles()[r['projectRoleName']])
            for r in project_roles
        ]
