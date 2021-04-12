from labelbox.schema.project import Project
from labelbox.orm.db_object import DbObject
from labelbox.orm.model import Field, Relationship
from labelbox.schema.role import Role


class User(DbObject):
    """ A User is a registered Labelbox user (for example you) associated with
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

    def update_org_role(self, role: Role):
        """ Updated the `User`s organization role. 

        See client.get_roles() to get all valid roles

        Args:
            role (Role): The role that you want to set for this user.

        """

        # IF you convert a user from project level permissions to org permissions and then convert back, their permissions will remain for each individual project
        self.client.execute(
            """mutation SetOrganizationRolePyApi($userId: ID!, $roleId: ID!) { setOrganizationRole(data: {userId: $userId, roleId: $roleId}) { id name }}""",
            {
                "userId": self.uid,
                "roleId": role.uid
            })

    def remove_from_project(self, project: Project):
        """ Removes a User from a project. Only used for project based users.
        Project based user means their org role is "NONE"

        Args:
            project (Project): Project to remove user from

        """
        self.upsert_project_role(project, self.client.get_roles()['NONE'])

    def upsert_project_role(self, project: Project, role: Role):
        """ Updates or replaces a User's role in a project.

        Args:
            project (Project): The project to update the users permissions for
            role (Role): The role to assign to this user in this project.
        
        """
        org_role = self.org_role()
        if org_role.name.upper() != 'NONE':
            raise ValueError(
                "User is not project based and has access to all projects")

        if not isinstance(role, Role):
            raise TypeError(f"Must provide a `Role` object. Found {role}")

        if not isinstance(project, Project):
            raise TypeError(f"Must provide a `Project` object. Found {project}")

        self.client.execute(
            """mutation SetProjectMembershipPyApi($projectId: ID!, $userId: ID!, $roleId: ID!) {
                setProjectMembership(data: {userId: $userId, roleId: $roleId, projectId: $projectId}) {id}}
        """, {
                "projectId": project.uid,
                "roleId": role.uid,
                "userId": self.uid
            })
