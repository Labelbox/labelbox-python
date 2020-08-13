"""Client side object for interacting with the ontology."""
from labelbox.orm import query
from labelbox.orm.db_object import DbObject, Updateable, BulkDeletable
from labelbox.orm.model import Entity, Field, Relationship


class Ontology(DbObject):
    """ A ontology specifies which tools and classifications are available
    to a project.

    NOTE: This is read only for now.

    >>> project = client.get_project(name="<project_name>")
    >>> ontology = project.ontology()
    >>> ontology.normalized

    """

    name = Field.String("name")
    description = Field.String("description")
    updated_at = Field.DateTime("updated_at")
    created_at = Field.DateTime("created_at")
    normalized = Field.Json("normalized")
    object_schema_count = Field.Int("object_schema_count")
    classification_schema_count = Field.Int("classification_schema_count")

    projects = Relationship.ToMany("Project", True)
    created_by = Relationship.ToOne("User", False, "created_by")
