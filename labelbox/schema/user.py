from labelbox.orm.db_object import DbObject
from labelbox.orm.model import Field, Relationship
from pydantic import BaseModel

from enum import Enum


class Role(Enum):
    # Looks like this creates a "Project Based" Role at the Org level... So they have No Role at org level.
    # If this is None at the project level then they are removed from the project
    NONE = "ckk4kkc8b002m09198iyzvtmq"  
    LABELER = "ckk4kkc9a002u0919omkuoby8"
    REVIEWER = "ckk4kkcae00320919lpxtf306"
    TEAM_MANAGER = "ckk4kkcbc003a09192dkfe80h"
    ADMIN =  "ckk4kkcc9003i0919xa6wttcg"


class ProjectRole(BaseModel):
    projectId: str
    projectRoleId: Role



#class ProjectInvitee(DbObject):
#    role: ProjectRole




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

    # I actually think this is deprecated ...
    class MemberRole(Enum):
        # https://docs.labelbox.com/en/manage-team#member-roles 
        ADMIN = "cjlvi91a41aab0714677xp87h"
        TEAM_MANAGER =  "cjlvi919q1aa80714b7z3xuku"
        PROJECT_ADMIN = "cjmb6xy80f5vz0780u3mw2rj4"
        REVIEWER = "cjlvi919b1aa50714k75euii5"
        LABELER = "cjlvi914y1aa20714372uvzjv"


    updated_at = Field.DateTime("updated_at")
    created_at = Field.DateTime("created_at")
    email = Field.String("email")
    name = Field.String("nickname")
    nickname = Field.String("name")
    intercom_hash = Field.String("intercom_hash")
    picture = Field.String("picture")
    is_viewer = Field.Boolean("is_viewer")
    is_external_user = Field.Boolean("is_external_user")
    #Role is prob valid..
    
    # Relationships
    organization = Relationship.ToOne("Organization")
    created_tasks = Relationship.ToMany("Task", False, "created_tasks")
    projects = Relationship.ToMany("Project", False)
    org_role = Relationship.ToOne("OrgRole", False)


    def update_role(self, role, projects = []):
        # Note that this will not clear invites. Idk what happens if you make the user non project based
        # Also if the user is going from labeler to admin do they get removed from project assignments ?
        # What if they get flipped back do they need to get added to projects?
        return self.organization().invite_user(self, self.email, role, projects = projects)
    

    def add_to_project(self, project : "Project", role : Role):
        # Strictly add to projects (only for non admin level roles)
        org_role = self.org_role()
        if org_role.name not in {Role.LABELER.name, Role.REVIEWER.name}:
            raise ValueError("User is not project based and has access to all projects")
        self.update_role(org_role, projects = [project])

    
    def remove_from_project(self, project):
        # Use User.projects() to find all projects that the user is attached to
        # If the user is project based and this is the only project they are a member of then they need to reaccept an email invite..
        # Also needs to be tested..
        # Can a user delete themselves? We prob don't want that.. Could check with `assert self.client.get_user() != self.uid`
        org_role = self.org_role()
        if org_role.name not in {Role.LABELER.name, Role.REVIEWER.name}:
            raise ValueError("User is not project based and has access to all projects")

        query_str = """mutation RemoveUserFromProject($input: SetProjectMembershipInput!) {
            changeMembershipForProject(data: $input) {id role {id} user {id}}}"""
        args = {
            "input": {
                "userId": self.uid,
                "projectId": project.uid,
                "roleId":  Role.NONE.value
                }
        }
        return self.client.execute(query_str, args, experimental = True)
            
 


    
class OrgRole(DbObject):
    name = Field.String("name")
