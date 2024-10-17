from labelbox.orm.db_object import DbObject
from labelbox.orm.model import Field, Relationship


class LabelingFrontend(DbObject):
    """Private db object representing a projects label editor"""

    name = Field.String("name")
    description = Field.String("description")
    iframe_url_path = Field.String("iframe_url_path")


class LabelingFrontendOptions(DbObject):
    """Label interface options.

    Attributes:
        customization_options (str)

        project (Relationship): `ToOne` relationship to Project
        labeling_frontend (Relationship): `ToOne` relationship to LabelingFrontend
        organization (Relationship): `ToOne` relationship to Organization
    """

    customization_options = Field.String("customization_options")

    project = Relationship.ToOne("Project")
    labeling_frontend = Relationship.ToOne("LabelingFrontend")
    organization = Relationship.ToOne("Organization")
