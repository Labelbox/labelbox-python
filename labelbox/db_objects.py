from enum import Enum

from labelbox import query, utils
from labelbox.schema import Field, DbObject

""" Defines client-side objects representing database content. """


def _create_relationship(destination_type_name, relationship_name=None):
    """ Creates a method to be used within a DbObject subtype for
    getting DB objects related to so source DB object.

    Args:
        destination_type_name (str): Name of the DbObject subtype that's
            on the other side of the relationship. Name is used instead
            of the type itself because the type might not be defined in
            the moment this function is called.
        relationship_name (str): Name of the relationship to expand. If
            None, then it's derived from `destionation_type_name` by
            converting to camelCase and adding "s".

    Return:
        A callable that accepts a single argument: the DB object that
            is the source of the relationship expansion. It must be
            an instance of a DbObject subtype.
    """
    if relationship_name is None:
        relationship_name = utils.camel_case(destination_type_name) + "s"

    def expansion(self):
        destination_type = next(
            t for t in DbObject.__subclasses__()
            if t.__name__.split(".")[-1] == destination_type_name)
        # TODO support filtering filter
        # TODO remove deleted objects from the other side
        query_string, id_param_name = query.relationship(
            self, relationship_name, destination_type)
        return query.PaginatedCollection(
            self.client, query_string, {id_param_name: self.uid},
            [utils.camel_case(type(self).type_name()), relationship_name],
            destination_type)

    return expansion


class Project(DbObject):
    # Rarely changing attributes.
    uid = Field("uid", "id")
    name = Field("name")
    description = Field("description")
    updated_at = Field("updated_at")
    created_at = Field("created_at")
    setupComplete = Field("setup_complete")

    # Relationships
    datasets = _create_relationship("Dataset")

    # TODO Relationships
    # organization
    # createdBy
    # datasets
    # labeledDatasets
    # labels
    # ...a lot more, define which are required for v0.1

    # TODO Mutable (fetched) attributes
    # ...many, define which are required for v0.1


class Dataset(DbObject):
    uid = Field("uid", "id")
    name = Field("name")
    updated_at = Field("updated_at")
    created_at = Field("created_at")

    # Relationships
    projects = _create_relationship("Project")

    # TODO Relationships
    # organization
    # createdBy
    # projects
    # dataRows

    # TODO Fetched attributes
    # rowCount
    # createdLabelCount
