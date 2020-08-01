from labelbox.orm.db_object import DbObject
from labelbox.orm.model import Field, Relationship


class LabelingFrontend(DbObject):
    """ Is a type representing an HTML / JavaScript UI that is used to generate
    labels. “Image Labeling” is the default Labeling Frontend that comes in every
    organization. You can create new labeling frontends for an organization.
    """
    name = Field.String("name")
    description = Field.String("description")
    iframe_url_path = Field.String("iframe_url_path")

    # TODO other fields and relationships
    projects = Relationship.ToMany("Project", True)


class LabelingFrontendOptions(DbObject):
    customization_options = Field.String("customization_options")

    project = Relationship.ToOne("Project")
    labeling_frontend = Relationship.ToOne("LabelingFrontend")
    organization = Relationship.ToOne("Organization")
