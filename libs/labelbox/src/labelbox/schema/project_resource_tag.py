from labelbox.orm.db_object import DbObject, Updateable
from labelbox.orm.model import Field, Relationship


class ProjectResourceTag(DbObject, Updateable):
    """Project resource tag to associate ProjectResourceTag to Project.

    Attributes:
        resourceTagId (str)
        projectId (str)

        resource_tag (Relationship): `ToOne` relationship to ResourceTag
    """

    resource_tag_id = Field.ID("resource_tag_id")
    project_id = Field.ID("project_id")
