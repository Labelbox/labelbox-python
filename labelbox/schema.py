from enum import Enum, auto

from labelbox import utils
from labelbox.exceptions import InvalidFieldError
from labelbox.filter import Comparison


""" Classes for defining the client-side data schema. """


class Field:
    """ Represents a field in a database table. Supports comparison operators
    which return a `labelbox.filter.Comparison` object. For example:
        >>> field = Field.String("x") # short for Field(Field.Type.String, "x")
        >>> comparison = field == "John"
        >>> print(comparison)

    These `Comparison` objects can then be used for filtering:
        >>> project = client.get_projects(comparison)

    Attributes:
        name (str): name that the attribute has in client-side Python objects
        grapgql_name (str): name that the attribute has in queries (and in
            server-side database definition).
    """

    class Type(Enum):
        """ Field type in GraphQL (server-side). """
        Int = auto()
        Float = auto()
        String = auto()
        Boolean = auto()
        ID = auto()
        DateTime = auto()

    class Order(Enum):
        Asc = auto()
        Desc = auto()

    @staticmethod
    def Int(*args):
        return Field(Field.Type.Int, *args)

    @staticmethod
    def Float(*args):
        return Field(Field.Type.Float, *args)

    @staticmethod
    def String(*args):
        return Field(Field.Type.String, *args)

    @staticmethod
    def Boolean(*args):
        return Field(Field.Type.Boolean, *args)

    @staticmethod
    def ID(*args):
        return Field(Field.Type.ID, *args)

    @staticmethod
    def DateTime(*args):
        return Field(Field.Type.DateTime, *args)

    def __init__(self, field_type, name, graphql_name=None):
        """ Field init.
        Args:
            field_type (Field.Type): The type of the field.
            name (str): client-side Python attribute name of a database
                object.
            graphql_name (str): query and server-side name of a database object.
                If None, it is constructed from the client-side name by converting
                snake_case (Python convention) into camelCase (GraphQL convention).
        """
        self.field_type = field_type
        self.name = name
        if graphql_name is None:
            graphql_name = utils.camel_case(name)
        self.graphql_name = graphql_name

    @property
    def asc(self):
        """ Property that resolves to tuple (Field, Field.Order).
        Used for easy definition of sort ordering:
            >>> projects_ordered = client.get_projects(order_by=Project.name.asc)
        """
        return (self, Field.Order.Asc)

    @property
    def desc(self):
        """ Property that resolves to tuple (Field, Field.Order).
        Used for easy definition of sort ordering:
            >>> projects_ordered = client.get_projects(order_by=Project.name.desc)
        """
        return (self, Field.Order.Desc)

    def __eq__(self, other):
        """ Equality of Fields has two meanings. If comparing to a Field object,
        then a boolean indicator if the fields are identical is returned. If
        comparing to any other type, a Comparison object is created.
        """
        if isinstance(other, Field):
            return self is other

        return Comparison.Op.EQ(self, other)

    def __ne__(self, other):
        """ Equality of Fields has two meanings. If comparing to a Field object,
        then a boolean indicator if the fields are identical is returned. If
        comparing to any other type, a Comparison object is created.
        """
        if isinstance(other, Field):
            return self is not other

        return Comparison.Op.NE(self, other)

    def __hash__(self):
        # Hash is implemeted as ID, because for each DB field exactly one
        # Field object should exist in the Python API.
        return id(self)

    def __lt__(self, other):
        return Comparison.Op.LT(self, other)

    def __gt__(self, other):
        return Comparison.Op.GT(self, other)

    def __le__(self, other):
        return Comparison.Op.LE(self, other)

    def __ge__(self, other):
        return Comparison.Op.GE(self, other)

    def __str__(self):
        return self.name

    def __repr__(self):
        return "<Field: %r>" % self.name


class Relationship:
    """ Represents a relationship in a database table.

    Attributes:
        relationship_type (Relationship.Type): Indicator if to-one or to-many
        destination_type_name (str): Name of the DbObject subtype that's on
            the other side of the relationship. str is used instead of the
            type object itself because that type might not be declared at
            the point of a `Relationship` object initialization.
        filter_deleted (bool): Indicator if the a `deleted=false` filtering
            clause should be added to the query when fetching relationship
            objects.
        name (str): Name of the relationship in the snake_case format.
    """
    class Type(Enum):
        ToOne = auto()
        ToMany = auto()

    @staticmethod
    def ToOne(*args):
        return Relationship(Relationship.Type.ToOne, *args)

    @staticmethod
    def ToMany(*args):
        return Relationship(Relationship.Type.ToMany, *args)

    def __init__(self, relationship_type, destination_type_name,
                 filter_deleted=True, name=None):
        self.relationship_type = relationship_type
        self.destination_type_name = destination_type_name
        self.filter_deleted = filter_deleted
        if name is None:
            name = utils.snake_case(destination_type_name) + (
                "s" if relationship_type == Relationship.Type.ToMany else "")
        self.name = name


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

    # Every DbObject has an "id" and a "deleted" field
    # Name the "id" field "uid" in Python to avoid conflict with keyword.
    uid = Field.ID("uid", "id")
    deleted = Field.Boolean("deleted")

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
    def _attributes_of_type(cls, attr_type):
        """ Yields all the attributes in `cls` of the given `attr_type`. """
        for attr_name in dir(cls):
            attr = getattr(cls, attr_name)
            if isinstance(attr, attr_type):
                yield attr

    @classmethod
    def fields(cls):
        """ Yields all the Fields declared in a concrete subclass. """
        for attr in cls._attributes_of_type(Field):
            if attr != DbObject.deleted:
                yield attr

    @classmethod
    def relationships(cls):
        return cls._attributes_of_type(Relationship)

    @classmethod
    def field(cls, field_name):
        """ Returns a Field object for the given name.
        Args:
            field_name (str): Field name, Python (snake-case) convention.
        Return:
            Field object
        Raises:
            InvalidFieldError: in case this DB object type does not contain
                a field with the given name.
        """
        field_obj = getattr(cls, field_name, None)
        if not isinstance(field_obj, Field):
            raise InvalidFieldError(cls, field_name)
        return field_obj

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
