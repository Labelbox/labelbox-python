from enum import Enum

from labelbox import utils


""" Classes for defining the client-side data schema. """


class Field:
    """ Represents field in a database table.

    Attributes:
        name (str): name that the attribute has in client-side Python objects
        grapgql_name (str): name that the attribute has in queries (and in
            server-side database definition).
    """
    def __init__(self, name, graphql_name=None):
        """ Field constructor.
        Args:
            name (str): client-side Python attribute name of a database
                object.
            graphql_name (str): query and server-side name of a database object.
                If None, it is constructed from the client-side name by converting
                snake_case (Python convention) into camelCase (GraphQL convention).
        """
        self.name = name
        if graphql_name is None:
            graphql_name = utils.camel_case(name)
        self.graphql_name = graphql_name


class DbObject:
    """ A client-side representation of a database object (row). Intended as
    base class for classes representing concrete database types (for example
    a Project). Exposes support functionalities so that the concrete subclass
    definition be as simple and DRY as possible. It should come down to just
    listing Fields of that particular database type. For example:
        >>> class Project(DbObject):
        >>>     uid = Field("uid", "id")
        >>>     name = Field("name")
        >>>     description = Field("description")
    """

    def __init__(self, client, field_values):
        """ Constructor of a database object. Generally it should only be used
        by library internals and not by the end user.

        Args:
            client (labelbox.Client): the client used for fetching data from DB.
            field_values (dict): Data obtained from the DB. Maps database object
                fields (their graphql_name version) to values.
        """
        self.client = client
        for field in type(self).fields():
            setattr(self, field.name, field_values[field.graphql_name])

    @classmethod
    def fields(cls):
        """ Yields all the Fields declared in a concrete subclass. """
        for attr_name in dir(cls):
            attr = getattr(cls, attr_name)
            if isinstance(attr, Field):
                yield attr

    @classmethod
    def type_name(cls):
        """ Returns this DB object type name in TitleCase. For example:
            Project, DataRow, ...
        """
        return cls.__name__.split(".")[-1]

    def __repr__(self):
        type_name = type(self).type_name()
        if "uid" in dir(self):
            return "<%s ID: %s>" % (type_name, self.uid)
        else:
            return "<%s>" % type_name

    def __str__(self):
        # TODO discuss exact __repr__ and __str__ representations
        attribute_values = {field.name: getattr(self, field.name)
                            for field in type(self).fields()}
        return "<%s %s>" % (type(self).type_name().split(".")[-1],
                                attribute_values)
