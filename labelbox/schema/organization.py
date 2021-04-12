from typing import Any, Dict, List

from labelbox.schema.invite import Invite, InviteLimit, UserLimit
from labelbox.schema.role import Role
from labelbox.exceptions import LabelboxError
from labelbox import utils
from labelbox.pagination import PaginatedCollection
from labelbox.orm.db_object import DbObject
from labelbox.orm.model import Field, Relationship
from labelbox.schema.user import User
from labelbox.schema.role import Role, ProjectRole


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

    def invites(self) -> PaginatedCollection:
        """ List all current invitees
        
        Returns:
            A PaginatedCollection of Invite objects

        """
        query_str = """query GetOrgInvitationsPyApi($from: ID, $first: PageSize) {
                organization { id invites(from: $from, first: $first) { 
                    nodes { id createdAt organizationRoleName inviteeEmail } nextCursor }}}"""
        return PaginatedCollection(
            self.client,
            query_str, {}, ['organization', 'invites', 'nodes'],
            Invite,
            cursor_path=['organization', 'invites', 'nextCursor'],
            experimental=True)

    def _assign_user_role(self, email: str, role: Role,
                          project_roles: List[ProjectRole]) -> Dict[str, Any]:
        """
        Creates or updates users. This function shouldn't directly be called. 
        Use `Organization.invite_user`

        Note: that there is a really unclear foreign key error if you use an unsupported role.
        - This means that the `Roles` object is not getting the right ids
        """
        if self.client.get_user().email == email:
            raise ValueError("Cannot update your own role")

        query_str = """mutation createInvitesPyApi($data: [CreateInviteInput!]){
                    createInvites(data: $data){  invite { id createdAt organizationRoleName inviteeEmail}}}"""

        project_roles = [{
            "projectId": x.project.uid,
            "projectRoleId": x.role.uid
        } for x in project_roles]
        res = self.client.execute(
            query_str, {
                'data': [{
                    "inviterId": self.client.get_user().uid,
                    "inviteeEmail": email,
                    "organizationId": self.uid,
                    "organizationRoleId": role.uid,
                    "projects": project_roles
                }]
            },
            experimental=True)  # We prob want to return an invite
        # Could support bulk ops in the future
        invite_info = res['createInvites'][0]['invite']
        return invite_info

    def invite_user(self,
                    email: str,
                    role: Role,
                    project_roles: List[ProjectRole] = []) -> Invite:
        """
        Invite a new member to the org. This will send the user an email invite

        Args:
            email (str): email address of the user to invite
            role (Role): Role to assign to the user
            project_roles (List[ProjectRoles]): List of project roles to assign to the User (if they have a project based org role).

        Returns:
            Invite for the user

        """
        remaining_invites = self.invite_limit().remaining
        if remaining_invites == 0:
            if next(self.users((User.email == email) &
                               (User.deleted == True)), None) is None:
                raise LabelboxError(
                    "Invite(s) cannot be sent because you do not have enough available seats in your organization. "
                    "Please upgrade your account, revoke pending invitations or remove other users."
                )
        for invite in self.invites():
            if invite.email == email:
                raise ValueError(
                    f"Invite already exists for {email}. Please revoke the invite if you want to update the role or resend."
                )

        if not isinstance(role, Role):
            raise TypeError(f"role must be Role type. Found {role}")

        if len(project_roles) and role.name != "NONE":
            raise ValueError(
                "Project roles cannot be set for a user with organization level permissions. Found role name `{role.name}`, expected `NONE`"
            )

        for project_role in project_roles:
            if not isinstance(project_role, ProjectRole):
                raise TypeError(
                    f"project_roles must be a list of `ProjectRole`s. Found {project_role}"
                )

        invite_response = self._assign_user_role(email, role, project_roles)
        return Invite(self.client, invite_response)

    def user_limit(self) -> UserLimit:
        """ Retrieve user limits for the org

        Returns:
            UserLimit
    
        """
        query_str = """query UsersLimitPyApi { 
            organization {id account { id usersLimit { dateLimitWasReached remaining used limit }}}}
        """
        res = self.client.execute(query_str, experimental=True)
        return UserLimit(
            **{
                utils.snake_case(k): v for k, v in res['organization']
                ['account']['usersLimit'].items()
            })

    def invite_limit(self) -> InviteLimit:
        """ Retrieve invite limits for the org
        This already accounts for users currently in the org
        Meaining that  `used = users + invites, remaining = limit - (users + invites)`
       
        Returns:
            InviteLimit
    
        """

        res = self.client.execute(
            """query InvitesLimitPyApi($organizationId: ID!) {
            invitesLimit(where: {id: $organizationId}) { used limit remaining }
        }""", {"organizationId": self.uid},
            experimental=True)
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

        self.client.execute(
            """mutation DeleteMemberPyApi($id: ID!) {
            updateUser(where: {id: $id}, data: {deleted: true}) { id deleted }
        }""", {'id': user.uid})
