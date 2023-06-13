import json
from typing import TYPE_CHECKING, List, Optional, Dict

from labelbox.exceptions import LabelboxError
from labelbox import utils
from labelbox.orm.db_object import DbObject, query, Entity
from labelbox.orm.model import Field, Relationship
from labelbox.schema.invite import InviteLimit
from labelbox.schema.resource_tag import ResourceTag

if TYPE_CHECKING:
    from labelbox import Role, User, ProjectRole, Invite, InviteLimit, IAMIntegration


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
    resource_tags = Relationship.ToMany("ResourceTags", False)

    def invite_user(
            self,
            email: str,
            role: "Role",
            project_roles: Optional[List["ProjectRole"]] = None) -> "Invite":
        """
        Invite a new member to the org. This will send the user an email invite

        Args:
            email (str): email address of the user to invite
            role (Role): Role to assign to the user
            project_roles (Optional[List[ProjectRoles]]): List of project roles to assign to the User (if they have a project based org role).

        Returns:
            Invite for the user

        Notes:
            1. Multiple invites can be sent for the same email. This can only be resolved in the UI for now.
                - Future releases of the SDK will support the ability to query and revoke invites to solve this problem (and/or checking on the backend)
            2. Some server side response are unclear (e.g. if the user invites themself `None` is returned which the SDK raises as a `LabelboxError` )
        """

        if project_roles and role.name != "NONE":
            raise ValueError(
                f"Project roles cannot be set for a user with organization level permissions. Found role name `{role.name}`, expected `NONE`"
            )

        data_param = "data"
        query_str = """mutation createInvitesPyApi($%s: [CreateInviteInput!]){
                    createInvites(data: $%s){  invite { id createdAt organizationRoleName inviteeEmail inviter { %s } }}}""" % (
            data_param, data_param, query.results_query_part(Entity.User))

        projects = [{
            "projectId": project_role.project.uid,
            "projectRoleId": project_role.role.uid
        } for project_role in project_roles or []]

        res = self.client.execute(
            query_str, {
                data_param: [{
                    "inviterId": self.client.get_user().uid,
                    "inviteeEmail": email,
                    "organizationId": self.uid,
                    "organizationRoleId": role.uid,
                    "projects": projects
                }]
            })
        invite_response = res['createInvites'][0]['invite']
        if not invite_response:
            raise LabelboxError(f"Unable to send invite for email {email}")
        return Entity.Invite(self.client, invite_response)

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

    def remove_user(self, user: "User") -> None:
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

    def create_resource_tag(self, tag: Dict[str, str]) -> ResourceTag:
        """
        Creates a resource tag.
            >>> tag = {'text': 'tag-1',  'color': 'ffffff'}

        Args:
            tag (dict): A resource tag {'text': 'tag-1', 'color': 'fffff'}
        Returns:
            The created resource tag.
        """
        tag_text_param = "text"
        tag_color_param = "color"

        query_str = """mutation CreateResourceTagPyApi($text:String!,$color:String!) {
                createResourceTag(input:{text:$%s,color:$%s}) {%s}}
        """ % (tag_text_param, tag_color_param,
               query.results_query_part(ResourceTag))

        params = {
            tag_text_param: tag.get("text", None),
            tag_color_param: tag.get("color", None)
        }
        if not all(params.values()):
            raise ValueError(
                f"tag must contain 'text' and 'color' keys. received: {tag}")

        res = self.client.execute(query_str, params)
        return ResourceTag(self.client, res['createResourceTag'])

    def get_resource_tags(self) -> List[ResourceTag]:
        """
        Returns all resource tags for an organization
        """
        query_str = """query GetOrganizationResourceTagsPyApi{organization{resourceTag{%s}}}""" % (
            query.results_query_part(ResourceTag))

        return [
            ResourceTag(self.client, tag) for tag in self.client.execute(
                query_str)['organization']['resourceTag']
        ]

    def get_iam_integrations(self) -> List["IAMIntegration"]:
        """
        Returns all IAM Integrations for an organization
        """
        res = self.client.execute(
            """query getAllIntegrationsPyApi { iamIntegrations {
                %s
                settings {
                __typename
                ... on AwsIamIntegrationSettings {roleArn}
                ... on GcpIamIntegrationSettings {serviceAccountEmailId readBucket}
                }

            } } """ % query.results_query_part(Entity.IAMIntegration))
        return [
            Entity.IAMIntegration(self.client, integration_data)
            for integration_data in res['iamIntegrations']
        ]

    def get_default_iam_integration(self) -> Optional["IAMIntegration"]:
        """
        Returns the default IAM integration for the organization.
        Will return None if there are no default integrations for the org.
        """
        integrations = self.get_iam_integrations()
        default_integration = [
            integration for integration in integrations
            if integration.is_org_default
        ]
        if len(default_integration) > 1:
            raise ValueError(
                "Found more than one default signer. Please contact Labelbox to resolve"
            )
        return None if not len(
            default_integration) else default_integration.pop()
