from dataclasses import dataclass
from typing import Optional
from datetime import datetime

from labelbox.orm.db_object import DbObject
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


@dataclass
class UserLimit(InviteLimit):
    """
    remaining(int): Remaining number of users that an org is allowed to have
    used (int): Total number of users in the org
    limit (int): Maximum number of users available to the org
    date_limit_was_reached (date): Date that `limit` was equal to `used`
    """
    date_limit_was_reached: Optional[datetime]


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

    def revoke(self):
        """ Makes the invitation invalid.
        """
        query_str = """mutation CancelInvitePyApi($where: WhereUniqueIdInput!) {
               cancelInvite(where: $where) {id}}"""
        self.client.execute(query_str, {'where': {
            'id': self.uid
        }},
                            experimental=True)
