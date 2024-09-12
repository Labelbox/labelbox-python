from labelbox.orm.db_object import DbObject, Updateable
from labelbox.orm.model import Field, Relationship


class ResourceTag(DbObject, Updateable):
    """Resource tag to label and identify your labelbox resources easier.

    Attributes:
        text (str)
        color (str)

        project_resource_tag (Relationship): `ToMany` relationship to ProjectResourceTag
    """

    text = Field.String("text")
    color = Field.String("color")
