from dataclasses import dataclass
from enum import Enum, auto
from typing import Dict, List, Union, Any, Type, TYPE_CHECKING

import labelbox
from labelbox import utils
from labelbox.exceptions import InvalidAttributeError
from labelbox.orm.comparison import Comparison

""" Defines Field, Relationship and Entity. These classes are building
blocks for defining the Labelbox schema, DB object operations and
queries. """


class Field:
    """Represents a field in a database table. A Field has a name, a type
    (corresponds to server-side GraphQL type) and a server-side name. The
    server-side name is most often just a camelCase version of the client-side
    snake_case name.

    Supports comparison operators which return a `labelbox.comparison.Comparison`
    object. For example:
        >>> class Project:
        >>>     name = Field.String("name")
        >>>
        >>> comparison = Project.name == "MyProject"

    These `Comparison` objects can then be used for filtering:
        >>> project = client.get_projects(comparison)

    Also exposes the ordering property used for sorting:
        >>> labels = project.labels(order_by=Label.label.asc)

    Attributes:
        field_type (Field.Type): The type of the field.
        name (str): name that the attribute has in client-side Python objects
        graphql_name (str): name that the attribute has in queries (and in
            server-side database definition).
        result_subquery (str): graphql query result payload for a field.
    """

    class Type(Enum):
        Int = auto()
        Float = auto()
        String = auto()
        Boolean = auto()
        ID = auto()
        DateTime = auto()
        Json = auto()

    class EnumType:
        def __init__(self, enum_cls: type):
            self.enum_cls = enum_cls

        @property
        def name(self):
            return self.enum_cls.__name__

    class ListType:
        """Represents Field that is a list of some object.
        Args:
            list_cls (type): Type of object that list is made of.
            graphql_type (str): Inner object's graphql type.
                By default, the list_cls's name is used as the graphql type.
        """

        def __init__(self, list_cls: type, graphql_type=None):
            self.list_cls = list_cls
            if graphql_type is None:
                self.graphql_type = self.list_cls.__name__
            else:
                self.graphql_type = graphql_type

        @property
        def name(self):
            return f"[{self.graphql_type}]"

    class Order(Enum):
        """Type of sort ordering."""

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

    @staticmethod
    def Enum(enum_cls: type, *args):
        return Field(Field.EnumType(enum_cls), *args)

    @staticmethod
    def Json(*args):
        return Field(Field.Type.Json, *args)

    @staticmethod
    def List(list_cls: type, graphql_type=None, **kwargs):
        return Field(Field.ListType(list_cls, graphql_type), **kwargs)

    def __init__(
        self,
        field_type: Union[Type, EnumType, ListType],
        name,
        graphql_name=None,
        result_subquery=None,
    ):
        """Field init.
        Args:
            field_type (Field.Type): The type of the field.
            name (str): client-side Python attribute name of a database
                object.
            graphql_name (str): query and server-side name of a database object.
                If None, it is constructed from the client-side name by converting
                snake_case (Python convention) into camelCase (GraphQL convention).
            result_subquery (str): graphql query result payload for a field.
        """
        self.field_type = field_type
        self.name = name
        if graphql_name is None:
            graphql_name = utils.camel_case(name)
        self.graphql_name = graphql_name
        self.result_subquery = result_subquery

    @property
    def asc(self):
        """Property that resolves to tuple (Field, Field.Order).
        Used for easy definition of sort ordering:
            >>> projects_ordered = client.get_projects(order_by=Project.name.asc)
        """
        return (self, Field.Order.Asc)

    @property
    def desc(self):
        """Property that resolves to tuple (Field, Field.Order).
        Used for easy definition of sort ordering:
            >>> projects_ordered = client.get_projects(order_by=Project.name.desc)
        """
        return (self, Field.Order.Desc)

    def __eq__(self, other):
        """Equality of Fields has two meanings. If comparing to a Field object,
        then a boolean indicator if the fields are identical is returned. If
        comparing to any other type, a Comparison object is created.
        """
        if isinstance(other, Field):
            return self is other

        return Comparison.Op.EQ(self, other)

    def __ne__(self, other):
        """Equality of Fields has two meanings. If comparing to a Field object,
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
    """Represents a relationship in a database table.

    Attributes:
        relationship_type (Relationship.Type): Indicator if to-one or to-many
        destination_type_name (str): Name of the Entity subtype that's on
            the other side of the relationship. str is used instead of the
            type object itself because that type might not be declared at
            the point of a `Relationship` object initialization.
        filter_deleted (bool): Indicator if the a `deleted=false` filtering
            clause should be added to the query when fetching relationship
            objects.
        name (str): Name of the relationship in the snake_case format.
        graphql_name (str): Name of the relationships server-side. Most often
            (not always) just a camelCase version of `name`.
        cache (bool) : Whether or not to cache the relationship values.
            Useful for objects that aren't directly queryable from the api (relationship query builder won't work)
            Also useful for expensive ToOne relationships
        deprecation_warning (string) optional message to display when RelationshipManager is called

    """

    @dataclass
    class Config:
        disconnect_supported: bool = True

    class Type(Enum):
        ToOne = auto()
        ToMany = auto()

    @staticmethod
    def ToOne(*args, **kwargs):
        return Relationship(Relationship.Type.ToOne, *args, **kwargs)

    @staticmethod
    def ToMany(*args, **kwargs):
        return Relationship(Relationship.Type.ToMany, *args, **kwargs)

    def __init__(
        self,
        relationship_type,
        destination_type_name,
        filter_deleted=True,
        name=None,
        graphql_name=None,
        cache=False,
        deprecation_warning=None,
        config=Config(),
    ):
        self.relationship_type = relationship_type
        self.destination_type_name = destination_type_name
        self.filter_deleted = filter_deleted
        self.cache = cache
        self.deprecation_warning = deprecation_warning
        self.config = config

        if name is None:
            name = utils.snake_case(destination_type_name) + (
                "s" if relationship_type == Relationship.Type.ToMany else ""
            )
        self.name = name

        if graphql_name is None:
            graphql_name = utils.camel_case(name)
        self.graphql_name = graphql_name

    @property
    def destination_type(self):
        return getattr(Entity, self.destination_type_name)

    def __str__(self):
        return self.name

    def __repr__(self):
        return "<Relationship: %r>" % self.name


class EntityMeta(type):
    """Entity metaclass. Registers Entity subclasses as attributes
    of the Entity class object so they can be referenced for example like:
        Entity.Project.
    """

    # Maps Entity name to Relationships for all currently defined Entities
    relationship_mappings: Dict[str, List[Relationship]] = {}

    def __setattr__(self, key: Any, value: Any):
        super().__setattr__(key, value)

    def __init__(cls, clsname, superclasses, attributedict):
        super().__init__(clsname, superclasses, attributedict)
        cls.validate_cached_relationships()
        if clsname != "Entity":
            setattr(Entity, clsname, cls)
            EntityMeta.relationship_mappings[utils.snake_case(cls.__name__)] = (
                cls.relationships()
            )

    @staticmethod
    def raise_for_nested_cache(first: str, middle: str, last: List[str]):
        raise TypeError(
            "Cannot cache a relationship to an Entity with its own cached relationship(s). "
            f"`{first}` caches `{middle}` which caches `{last}`"
        )

    @staticmethod
    def cached_entities(entity_name: str):
        """
        Return all cached entites for a given Entity name
        """
        cached_entities = EntityMeta.relationship_mappings.get(entity_name, [])
        return {
            entity.name: entity for entity in cached_entities if entity.cache
        }

    def validate_cached_relationships(cls):
        """
        Graphql doesn't allow for infinite nesting in queries.
        This function checks that cached relationships result in valid queries.
            * It does this by making sure that a cached relationship do not
              reference any entity with its own cached relationships.

        This check is performed by looking to see if this entity caches
        any entities that have their own cached fields. If this entity
        that we are checking has any cached fields then we also check
        all currently defined entities to see if they cache this entity.

        A two way check is necessary because checks are performed as classes are being defined.
        As opposed to after all objects have been created.
        """
        # All cached relationships
        cached_rels = [r for r in cls.relationships() if r.cache]

        # Check if any cached entities have their own cached fields
        for rel in cached_rels:
            nested = cls.cached_entities(rel.name)
            if nested:
                cls.raise_for_nested_cache(
                    utils.snake_case(cls.__name__),
                    rel.name,
                    list(nested.keys()),
                )

        # If the current Entity (cls) has any cached relationships (cached_rels)
        #  then no other defined Entity (entities in EntityMeta.relationship_mappings) can cache this Entity.
        if cached_rels:
            # For all currently defined Entities
            for entity_name in EntityMeta.relationship_mappings:
                # Get all cached ToOne relationships
                rels = cls.cached_entities(entity_name)
                # Check if the current Entity (cls) is referenced by the Entity with `entity_name`
                rel = rels.get(utils.snake_case(cls.__name__))
                # If rel exists and is cached then raise an exception
                # This means `entity_name` caches `cls` which cached items in `cached_rels`
                if rel and rel.cache:
                    cls.raise_for_nested_cache(
                        utils.snake_case(entity_name),
                        utils.snake_case(cls.__name__),
                        [entity.name for entity in cached_rels],
                    )


class Entity(metaclass=EntityMeta):
    """An entity that contains fields and relationships. Base class
    for DbObject (which is base class for concrete schema classes)."""

    # Every Entity has an "id" and a "deleted" field
    # Name the "id" field "uid" in Python to avoid conflict with keyword.
    uid = Field.ID("uid", "id")

    # Some Labelbox objects have a "deleted" attribute for soft deletions.
    # It's declared in Entity so it can be filtered out in class methods
    # suchs as `fields()`.
    deleted = Field.Boolean("deleted")

    if TYPE_CHECKING:
        DataRow: Type[labelbox.DataRow]
        Webhook: Type[labelbox.Webhook]
        Task: Type[labelbox.Task]
        AssetAttachment: Type[labelbox.AssetAttachment]
        ModelRun: Type[labelbox.ModelRun]
        ModelConfig: Type[labelbox.ModelConfig]
        Review: Type[labelbox.Review]
        User: Type[labelbox.User]
        LabelingFrontend: Type[labelbox.LabelingFrontend]
        BulkImportRequest: Type[labelbox.BulkImportRequest]
        Benchmark: Type[labelbox.Benchmark]
        IAMIntegration: Type[labelbox.IAMIntegration]
        LabelingFrontendOptions: Type[labelbox.LabelingFrontendOptions]
        Label: Type[labelbox.Label]
        MEAPredictionImport: Type[labelbox.MEAPredictionImport]
        MALPredictionImport: Type[labelbox.MALPredictionImport]
        Invite: Type[labelbox.Invite]
        InviteLimit: Type[labelbox.InviteLimit]
        ProjectRole: Type[labelbox.ProjectRole]
        ProjectModelConfig: Type[labelbox.ProjectModelConfig]
        Project: Type[labelbox.Project]
        Batch: Type[labelbox.Batch]
        CatalogSlice: Type[labelbox.CatalogSlice]
        ModelSlice: Type[labelbox.ModelSlice]
        TaskQueue: Type[labelbox.TaskQueue]

    @classmethod
    def _attributes_of_type(cls, attr_type):
        """Yields all the attributes in `cls` of the given `attr_type`."""
        for attr_name in dir(cls):
            attr = getattr(cls, attr_name)
            if isinstance(attr, attr_type):
                yield attr

    @classmethod
    def fields(cls):
        """Returns a generator that yields all the Fields declared in a
        concrete subclass.
        """
        for attr in cls._attributes_of_type(Field):
            if attr != Entity.deleted:
                yield attr

    @classmethod
    def relationships(cls):
        """Returns a generator that yields all the Relationships declared in
        a concrete subclass.
        """
        return cls._attributes_of_type(Relationship)

    @classmethod
    def field(cls, field_name):
        """Returns a Field object for the given name.
        Args:
            field_name (str): Field name, Python (snake-case) convention.
        Return:
            Field object
        Raises:
            InvalidAttributeError: in case this DB object type does not
            contain a field with the given name.
        """
        field_obj = getattr(cls, field_name, None)
        if not isinstance(field_obj, Field):
            raise InvalidAttributeError(cls, field_name)
        return field_obj

    @classmethod
    def attribute(cls, attribute_name):
        """Returns a Field or a Relationship object for the given name.
        Args:
            attribute_name (str): Field or Relationship name, Python
                (snake-case) convention.
        Return:
            Field or Relationship object
        Raises:
            InvalidAttributeError: in case this DB object type does not
                contain an attribute with the given name.
        """
        attribute_object = getattr(cls, attribute_name, None)
        if not isinstance(attribute_object, (Field, Relationship)):
            raise InvalidAttributeError(cls, attribute_name)
        return attribute_object

    @classmethod
    def type_name(cls):
        """Returns this DB object type name in TitleCase. For example:
        Project, DataRow, ...
        """
        return cls.__name__.split(".")[-1]
