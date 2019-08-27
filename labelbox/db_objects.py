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

    def expansion(self, where=None):
        destination_type = next(
            t for t in DbObject.__subclasses__()
            if t.__name__.split(".")[-1] == destination_type_name)
        query_string, params = query.relationship(
            self, relationship_name, destination_type, where)
        return query.PaginatedCollection(
            self.client, query_string, params,
            [utils.camel_case(type(self).type_name()), relationship_name],
            destination_type)

    return expansion


class Project(DbObject):
    name = Field.String("name")
    description = Field.String("description")
    updated_at = Field.DateTime("updated_at")
    created_at = Field.DateTime("created_at")
    setup_complete = Field.DateTime("setup_complete")

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
    name = Field.String("name")
    updated_at = Field.DateTime("updated_at")
    created_at = Field.DateTime("created_at")

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
