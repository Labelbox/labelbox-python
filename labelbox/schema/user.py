from labelbox.orm.db_object import DbObject
from labelbox.orm.model import Field, Relationship


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
