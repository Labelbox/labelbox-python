from labelbox import query, utils
from labelbox.schema import Field, DbObject


""" Defines client-side objects representing database content. """


def _to_many(destination_type_name, filter_deleted, relationship_name=None):
    """ Creates a method to be used within a DbObject subtype for
    getting DB objects related to so source DB object in a to-many
    relationship.

    Args:
        destination_type_name (str): Name of the DbObject subtype that's
            on the other side of the relationship. Name is used instead
            of the type itself because the type might not be defined in
            the moment this function is called.
        filter_deleted (bool): If or not an implicit `where` clause should
            be added containing {`deleted`: false}. Required in some cases,
            but not available in others.
        relationship_name (str): Name of the relationship to expand. If
            None, then it's derived from `destionation_type_name` by
            converting to camelCase and adding "s".

    Return:
        A callable that accepts two arguments: the DB object that
            is the source of the relationship expansion and a "where"
            clause. It returns a callable used for querying a to-many
            relationship.
    """
    if relationship_name is None:
        relationship_name = utils.camel_case(destination_type_name) + "s"

    def expansion(self, where=None):
        destination_type = next(
            t for t in DbObject.__subclasses__()
            if t.__name__.split(".")[-1] == destination_type_name)

        if filter_deleted:
            not_deleted = destination_type.deleted == False
            where = not_deleted if where is None else where & not_deleted

        query_string, params = query.relationship(
            self, relationship_name, destination_type, True, where)
        return query.PaginatedCollection(
            self.client, query_string, params,
            [utils.camel_case(type(self).type_name()), relationship_name],
            destination_type)

    return expansion


def _to_one(destination_type_name, relationship_name=None):
    """ Creates a method to be used within a DbObject subtype for
    getting a DB object related to so source DB object in a to-one
    relationship.

    Args:
        destination_type_name (str): Name of the DbObject subtype that's
            on the other side of the relationship. Name is used instead
            of the type itself because the type might not be defined in
            the moment this function is called.
        relationship_name (str): Name of the relationship to expand. If
            None, then it's derived from `destionation_type_name` by
            converting to camelCase.

    Return:
        A callable that accepts a single argument: the DB object that
            is the source of the relationship expansion. It returns a callable
            used for querying a to-one relationship.
    """
    if relationship_name is None:
        relationship_name = utils.camel_case(destination_type_name)

    def expansion(self):
        destination_type = next(
            t for t in DbObject.__subclasses__()
            if t.__name__.split(".")[-1] == destination_type_name)

        query_string, params = query.relationship(
            self, relationship_name, destination_type, False, None)
        result = self.client.execute(query_string, params)["data"]
        result = result[utils.camel_case(type(self).type_name())]
        result = result[relationship_name]
        return destination_type(self.client, result)

    return expansion


class Project(DbObject):
    name = Field.String("name")
    description = Field.String("description")
    updated_at = Field.DateTime("updated_at")
    created_at = Field.DateTime("created_at")
    setup_complete = Field.DateTime("setup_complete")

    # Relationships
    datasets = _to_many("Dataset", True)

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
    projects = _to_many("Project", True)
    data_rows = _to_many("DataRow", False)

    # TODO Relationships
    # organization
    # createdBy
    # projects
    # dataRows

    # TODO Fetched attributes
    # rowCount
    # createdLabelCount


class DataRow(DbObject):
    external_id = Field.String("external_id")
    row_data = Field.String("row_data")
    updated_at = Field.DateTime("updated_at")
    created_at = Field.DateTime("created_at")

    # Relationships
    dataset = _to_one("Dataset", True)

    # TODO other attributes


class User(DbObject):
    updated_at = Field.DateTime("updated_at")
    created_at = Field.DateTime("created_at")
    email = Field.String("email")
    name = Field.String("nickname")
    nickname = Field.String("name")

    # Relationships
    organization = _to_one("Organization")

    # TODO other attributes


class Organization(DbObject):
    updated_at = Field.DateTime("updated_at")
    created_at = Field.DateTime("created_at")
    name = Field.String("name")

    # Relationships
    users = _to_many("user", False)

    # TODO other attributes
