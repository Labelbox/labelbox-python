from labelbox.orm.db_object import DbObject
from labelbox.orm.model import Field, Relationship


class LabelingFrontend(DbObject):
    """ Label editor.

    Represents an HTML / JavaScript UI that is used to generate
    labels. “Editor” is the default Labeling Frontend that comes in every
    organization. You can create new labeling frontends for an organization.

    Attributes:
        name (str)
        description (str)
        iframe_url_path (str)

        projects (Relationship): `ToMany` relationship to Project
    """
    name = Field.String("name")
    description = Field.String("description")
    iframe_url_path = Field.String("iframe_url_path")

    # TODO other fields and relationships
    projects = Relationship.ToMany("Project", True)


class LabelingFrontendOptions(DbObject):
    """ Label interface options.

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
