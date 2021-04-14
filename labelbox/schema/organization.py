from typing import List, Optional

from labelbox.exceptions import LabelboxError
from labelbox import utils
from labelbox.orm.db_object import DbObject, beta
from labelbox.orm.model import Field, Relationship
from labelbox.schema.invite import Invite, InviteLimit, ProjectRole
from labelbox.schema.user import User
from labelbox.schema.role import Role
import logging

logger = logging.getLogger(__name__)


class Organization(DbObject):
    """ An Organization is a group of Users.

    It is associated with data created by Users within that Organization.
    Typically all Users within an Organization have access to data created by any User in the same Organization.

    Attributes:
        updated_at (datetime)
        created_at (datetime)
        name (str)

        users (Relationship): `ToMany` relationship to User
        projects (Relationship): `ToMany` relationship to Project
        webhooks (Relationship): `ToMany` relationship to Webhook
    """

    # RelationshipManagers in Organization use the type in Query (and
    # not the source object) because the server-side does not support
    # filtering on ID in the query for getting a single organization.
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for relationship in self.relationships():
            getattr(self, relationship.name).filter_on_id = False

    updated_at = Field.DateTime("updated_at")
    created_at = Field.DateTime("created_at")
    name = Field.String("name")

    # Relationships
    users = Relationship.ToMany("User", False)
    projects = Relationship.ToMany("Project", True)
    webhooks = Relationship.ToMany("Webhook", False)

    @beta
    def invite_user(
            self,
            email: str,
            role: Role,
            project_roles: Optional[List[ProjectRole]] = None) -> Invite:
        """
        Invite a new member to the org. This will send the user an email invite

        Args:
            email (str): email address of the user to invite
            role (Role): Role to assign to the user
            project_roles (Optional[List[ProjectRoles]]): List of project roles to assign to the User (if they have a project based org role).

        Returns:
            Invite for the user

        Creates or updates users. This function shouldn't directly be called. 
        Use `Organization.invite_user`

        Note: that there is a really unclear foreign key error if you use an unsupported role.
        - This means that the `Roles` object is not getting the right ids
        """
        remaining_invites = self.invite_limit().remaining
        if remaining_invites == 0:
            raise LabelboxError(
                "Invite(s) cannot be sent because you do not have enough available seats in your organization. "
                "Please upgrade your account, revoke pending invitations or remove other users."
            )

        if not isinstance(role, Role):
            raise TypeError(f"role must be Role type. Found {role}")

        if project_roles and role.name != "NONE":
            raise ValueError(
                "Project roles cannot be set for a user with organization level permissions. Found role name `{role.name}`, expected `NONE`"
            )

        _project_roles = [] if project_roles is None else project_roles
        for project_role in _project_roles:
            if not isinstance(project_role, ProjectRole):
                raise TypeError(
                    f"project_roles must be a list of `ProjectRole`s. Found {project_role}"
                )

        if self.client.get_user().email == email:
            raise ValueError("Cannot update your own role")

        data_param = "data"
        query_str = """mutation createInvitesPyApi($%s: [CreateInviteInput!]){
                    createInvites(data: $%s){  invite { id createdAt organizationRoleName inviteeEmail}}}""" % (
            data_param, data_param)

        projects = [{
            "projectId": project_role.project.uid,
            "projectRoleId": project_role.role.uid
        } for project_role in _project_roles]

        res = self.client.execute(
            query_str,
            {
                data_param: [{
                    "inviterId": self.client.get_user().uid,
                    "inviteeEmail": email,
                    "organizationId": self.uid,
                    "organizationRoleId": role.uid,
                    "projects": projects
                }]
            },
        )
        # We prob want to return an invite
        # Could support bulk ops in the future
        invite_response = res['createInvites'][0]['invite']
        return Invite(self.client, invite_response)

    @beta
    def invite_limit(self) -> InviteLimit:
        """ Retrieve invite limits for the org
        This already accounts for users currently in the org
        Meaining that  `used = users + invites, remaining = limit - (users + invites)`
       
        Returns:
            InviteLimit
    
        """
        org_id_param = "organizationId"
        res = self.client.execute(
            """query InvitesLimitPyApi($%s: ID!) {
            invitesLimit(where: {id: $%s}) { used limit remaining }
        }""" % (org_id_param, org_id_param), {org_id_param: self.uid})
        return InviteLimit(
            **{utils.snake_case(k): v for k, v in res['invitesLimit'].items()})

    def remove_user(self, user: User):
        """
        Deletes a user from the organization. This cannot be undone without sending another invite.

        Args:
            user (User): The user to delete from the org
        """

        if not isinstance(user, User):
            raise TypeError(f"Expected user to be of type User, found {user}")

        user_id_param = "userId"
        self.client.execute(
            """mutation DeleteMemberPyApi($%s: ID!) {
            updateUser(where: {id: $%s}, data: {deleted: true}) { id deleted }
        }""" % (user_id_param, user_id_param), {user_id_param: user.uid})
