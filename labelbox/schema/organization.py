from typing import List, Optional

from labelbox.exceptions import LabelboxError
from labelbox import utils
from labelbox.orm.db_object import DbObject, experimental, query
from labelbox.orm.model import Field, Relationship
from labelbox.schema.invite import Invite, InviteLimit, ProjectRole
from labelbox.schema.user import User
from labelbox.schema.role import Role


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

    @experimental
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

        Notes:
            This function is currently experimental and has a few limitations that will be resolved in future releases
            1. If you try to add an unsupported you will get an error referring to invalid foreign keys
                - In this case `role.get_roles` is likely not getting the right ids
            2. Multiple invites can be sent for the same email. This can only be resolved in the UI for now.
                - Future releases of the SDK will support the ability to query and revoke invites to solve this problem (and/or checking on the backend)
            3. Some server side response are unclear (e.g. if the user invites themself `None` is returned which the SDK raises as a `LabelboxError` )
        """

        if project_roles and role.name != "NONE":
            raise ValueError(
                f"Project roles cannot be set for a user with organization level permissions. Found role name `{role.name}`, expected `NONE`"
            )

        data_param = "data"
        query_str = """mutation createInvitesPyApi($%s: [CreateInviteInput!]){
                    createInvites(data: $%s){  invite { id createdAt organizationRoleName inviteeEmail inviter { %s } }}}""" % (
            data_param, data_param, query.results_query_part(User))

        projects = [{
            "projectId": project_role.project.uid,
            "projectRoleId": project_role.role.uid
        } for project_role in project_roles or []]

        res = self.client.execute(query_str, {
            data_param: [{
                "inviterId": self.client.get_user().uid,
                "inviteeEmail": email,
                "organizationId": self.uid,
                "organizationRoleId": role.uid,
                "projects": projects
            }]
        },
                                  experimental=True)
        invite_response = res['createInvites'][0]['invite']
        if not invite_response:
            raise LabelboxError(f"Unable to send invite for email {email}")
        return Invite(self.client, invite_response)

    @experimental
    def invite_limit(self) -> InviteLimit:
        """ Retrieve invite limits for the org
        This already accounts for users currently in the org
        Meaining that  `used = users + invites, remaining = limit - (users + invites)`
       
        Returns:
            InviteLimit
    
        """
        org_id_param = "organizationId"
        res = self.client.execute("""query InvitesLimitPyApi($%s: ID!) {
            invitesLimit(where: {id: $%s}) { used limit remaining }
        }""" % (org_id_param, org_id_param), {org_id_param: self.uid},
                                  experimental=True)
        return InviteLimit(
            **{utils.snake_case(k): v for k, v in res['invitesLimit'].items()})

    def remove_user(self, user: User):
        """
        Deletes a user from the organization. This cannot be undone without sending another invite.

        Args:
            user (User): The user to delete from the org
        """

        user_id_param = "userId"
        self.client.execute(
            """mutation DeleteMemberPyApi($%s: ID!) {
            updateUser(where: {id: $%s}, data: {deleted: true}) { id deleted }
        }""" % (user_id_param, user_id_param), {user_id_param: user.uid})
