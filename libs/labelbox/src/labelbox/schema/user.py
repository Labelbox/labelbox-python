from typing import TYPE_CHECKING
from labelbox.orm.db_object import DbObject
from labelbox.orm.model import Field, Relationship

if TYPE_CHECKING:
    from labelbox import Role, Project


class User(DbObject):
    """A User is a registered Labelbox user (for example you) associated with
    data they create or import and an Organization they belong to.

    Attributes:
        updated_at (datetime)
        created_at (datetime)
        email (str)
        name (str)
        nickname (str)
        intercom_hash (str)
        picture (str)
        is_viewer (bool)
        is_external_viewer (bool)

        organization (Relationship): `ToOne` relationship to Organization
        created_tasks (Relationship): `ToMany` relationship to Task
        projects (Relationship): `ToMany` relationship to Project
    """

    updated_at = Field.DateTime("updated_at")
    created_at = Field.DateTime("created_at")
    email = Field.String("email")
    name = Field.String("nickname")
    nickname = Field.String("name")
    intercom_hash = Field.String("intercom_hash")
    picture = Field.String("picture")
    is_viewer = Field.Boolean("is_viewer")
    is_external_user = Field.Boolean("is_external_user")

    # Relationships
    organization = Relationship.ToOne("Organization")
    created_tasks = Relationship.ToMany("Task", False, "created_tasks")
    projects = Relationship.ToMany("Project", False)
    org_role = Relationship.ToOne("OrgRole", False)

    def update_org_role(self, role: "Role") -> None:
        """Updated the `User`s organization role.

        See client.get_roles() to get all valid roles
        If you a user is converted from project level permissions to org level permissions and then convert back, their permissions will remain for each individual project

        Args:
            role (Role): The role that you want to set for this user.

        """
        user_id_param = "userId"
        role_id_param = "roleId"
        query_str = """mutation SetOrganizationRolePyApi($%s: ID!, $%s: ID!) {
            setOrganizationRole(data: {userId: $userId, roleId: $roleId}) { id name }}
        """ % (user_id_param, role_id_param)

        self.client.execute(
            query_str, {user_id_param: self.uid, role_id_param: role.uid}
        )

    def remove_from_project(self, project: "Project") -> None:
        """Removes a User from a project. Only used for project based users.
        Project based user means their org role is "NONE"

        Args:
            project (Project): Project to remove user from

        """
        self.upsert_project_role(project, self.client.get_roles()["NONE"])

    def upsert_project_role(self, project: "Project", role: "Role") -> None:
        """Updates or replaces a User's role in a project.

        Args:
            project (Project): The project to update the users permissions for
            role (Role): The role to assign to this user in this project.

        """
        org_role = self.org_role()
        if org_role.name.upper() != "NONE":
            raise ValueError(
                "User is not project based and has access to all projects"
            )

        project_id_param = "projectId"
        user_id_param = "userId"
        role_id_param = "roleId"
        query_str = """mutation SetProjectMembershipPyApi($%s: ID!, $%s: ID!, $%s: ID!) {
                setProjectMembership(data: {%s: $userId, roleId: $%s, projectId: $%s}) {id}}
        """ % (
            user_id_param,
            role_id_param,
            project_id_param,
            user_id_param,
            role_id_param,
            project_id_param,
        )

        self.client.execute(
            query_str,
            {
                project_id_param: project.uid,
                user_id_param: self.uid,
                role_id_param: role.uid,
            },
        )
