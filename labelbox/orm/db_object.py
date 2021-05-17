from datetime import datetime, timezone
from functools import wraps
import logging

from labelbox import utils
from labelbox.exceptions import InvalidQueryError, InvalidAttributeError
from labelbox.orm import query
from labelbox.orm.model import Field, Relationship, Entity
from labelbox.pagination import PaginatedCollection

logger = logging.getLogger(__name__)


class DbObject(Entity):
    """ A client-side representation of a database object (row). Intended as
    base class for classes representing concrete database types (for example
    a Project). Exposes support functionalities so that the concrete subclass
    definition be as simple and DRY as possible. It should come down to just
    listing Fields of that particular database type. For example:

        >>> class Project(DbObject):
        >>>     name = Field.String("name")
        >>>     labels = Relationship.ToMany("Label", True)

    This defines a `Project` class that has class attributes which are
    `Field`s and `Relationship`s. An instance of `Project` represents
    a database record. It has the same attributes as the `Project` class,
    but they are now attribute values of that record:

        >>> project = client.create_project(name="MyProject")
        >>> project.name
        "MyProject"
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
        self._set_field_values(field_values)
        for relationship in self.relationships():
            value = field_values.get(utils.camel_case(relationship.name))
            if relationship.cache and value is None:
                raise KeyError(
                    f"Expected field  values for {relationship.name}")

            setattr(self, relationship.name,
                    RelationshipManager(self, relationship, value))

    def _set_field_values(self, field_values):
        """ Sets field values on this object. Ensures proper value conversions.
        Args:
            field_values (dict): Maps field names (GraphQL variant, snakeCase)
                to values. *Must* contain all field values for this object's
                DB type.
        """
        for field in self.fields():
            value = field_values[field.graphql_name]
            if field.field_type == Field.Type.DateTime and value is not None:
                try:
                    value = datetime.strptime(value, "%Y-%m-%dT%H:%M:%S.%fZ")
                    value = value.replace(tzinfo=timezone.utc)
                except ValueError:
                    logger.warning(
                        "Failed to convert value '%s' to datetime for "
                        "field %s", value, field)
            elif isinstance(field.field_type, Field.EnumType):
                value = field.field_type.enum_cls[value]
            setattr(self, field.name, value)

    def __repr__(self):
        type_name = self.type_name()
        if "uid" in self.__dict__:
            return "<%s ID: %s>" % (type_name, self.uid)
        else:
            return "<%s>" % type_name

    def __str__(self):
        attribute_values = {
            field.name: getattr(self, field.name) for field in self.fields()
        }
        return "<%s %s>" % (self.type_name().split(".")[-1], attribute_values)

    def __eq__(self, other):
        return (isinstance(other, DbObject) and
                self.type_name() == other.type_name() and self.uid == other.uid)

    def __hash__(self):
        return 7541 * hash(self.type_name()) + hash(self.uid)


class RelationshipManager:
    """ Manages relationships (object fetching and updates) for a `DbObject`
    instance. There is one RelationshipManager for each relationship in
    each `DbObject` instance.
    """

    def __init__(self, source, relationship, value=None):
        """Args:
            source (DbObject subclass instance): The object that's the source
                of the relationship.
            relationship (labelbox.schema.Relationship): The relationship
                schema descriptor object.
        """
        self.source = source
        self.relationship = relationship
        self.supports_filtering = True
        self.supports_sorting = True
        self.filter_on_id = True
        self.value = value

    def __call__(self, *args, **kwargs):
        """ Forwards the call to either `_to_many` or `_to_one` methods,
        depending on relationship type. """
        if self.relationship.relationship_type == Relationship.Type.ToMany:
            return self._to_many(*args, **kwargs)
        else:
            return self._to_one(*args, **kwargs)

    def _to_many(self, where=None, order_by=None):
        """ Returns an iterable over the destination relationship objects.
        Args:
            where (None, Comparison or LogicalExpression): Filtering clause.
            order_by (None or (Field, Field.Order)): Ordering clause.
        Return:
            iterable over destination DbObject instances.
        """
        rel = self.relationship

        if where is not None and not self.supports_filtering:
            raise InvalidQueryError(
                "Relationship %s.%s doesn't support filtering" %
                (self.source.type_name(), rel.name))
        if order_by is not None and not self.supports_sorting:
            raise InvalidQueryError(
                "Relationship %s.%s doesn't support sorting" %
                (self.source.type_name(), rel.name))

        if rel.filter_deleted:
            not_deleted = rel.destination_type.deleted == False
            where = not_deleted if where is None else where & not_deleted

        query_string, params = query.relationship(
            self.source if self.filter_on_id else type(self.source), rel, where,
            order_by)
        return PaginatedCollection(
            self.source.client, query_string, params,
            [utils.camel_case(self.source.type_name()), rel.graphql_name],
            rel.destination_type)

    def _to_one(self):
        """ Returns the relationship destination object. """
        rel = self.relationship

        if self.value:
            return rel.destination_type(self.source.client, self.value)

        query_string, params = query.relationship(self.source, rel, None, None)
        result = self.source.client.execute(query_string, params)
        result = result and result.get(
            utils.camel_case(type(self.source).type_name()))
        result = result and result.get(rel.graphql_name)
        if result is None:
            return None

        return rel.destination_type(self.source.client, result)

    def connect(self, other):
        """ Connects source object of this manager to the `other` object. """
        query_string, params = query.update_relationship(
            self.source, other, self.relationship, "connect")
        self.source.client.execute(query_string, params)

    def disconnect(self, other):
        """ Disconnects source object of this manager from the `other` object. """
        query_string, params = query.update_relationship(
            self.source, other, self.relationship, "disconnect")
        self.source.client.execute(query_string, params)


class Updateable:

    def update(self, **kwargs):
        """ Updates this DB object with new values. Values should be
        passed as key-value arguments with field names as keys:
            >>> db_object.update(name="New name", title="A title")

        Kwargs:
            Key-value arguments defining which fields should be updated
            for which values. Keys must be field names in this DB object's
            type.
        Raise:
            InvalidAttributeError: if there exists a key in `kwargs`
                that's not a field in this object type.
        """
        values = {self.field(name): value for name, value in kwargs.items()}
        invalid_fields = set(values) - set(self.fields())
        if invalid_fields:
            raise InvalidAttributeError(type(self), invalid_fields)

        query_string, params = query.update_fields(self, values)
        res = self.client.execute(query_string, params)
        res = res["update%s" % utils.title_case(self.type_name())]
        self._set_field_values(res)


class Deletable:
    """ Implements deletion for objects that have a `deleted` attribute. """

    def delete(self):
        """ Deletes this DB object from the DB (server side). After
        a call to this you should not use this DB object anymore.
        """
        query_string, params = query.delete(self)
        self.client.execute(query_string, params)


class BulkDeletable:
    """ Implements deletion for objects that have a custom, bulk deletion
    mutation (accepts a list of IDs of objects to be deleted).

    A subclass must override the `bulk_delete` static method so it
    accepts only the `objects` argument and then invoke BulkDeletable.bulk_delete
    with the appropriate `use_where_clause` argument for that particular
    type.
    """

    @staticmethod
    def _bulk_delete(objects, use_where_clause):
        """
        Args:
            objects (list): Objects to delete. All objects must be of the same
                DbObject subtype.
            use_where_clause (bool): If the GraphQL query object IDs should be
                passed under `where` or directly. Necessary because the bulk
                deletion mutation is implemented differently for different
                object types (DataRow.bulkDelete vs Label.bulkDelete).
        """
        types = {type(o) for o in objects}
        if len(types) != 1:
            raise InvalidQueryError(
                "Can't bulk-delete objects of different types: %r" % types)

        query_str, params = query.bulk_delete(objects, use_where_clause)
        objects[0].client.execute(query_str, params)

    def delete(self):
        """ Deletes this DB object from the DB (server side). After
        a call to this you should not use this DB object anymore.
        """
        type(self).bulk_delete([self])


def experimental(fn):

    @wraps(fn)
    def wrapper(self, *args, **kwargs):
        if not self.client.enable_experimental:
            raise Exception(
                f"This function {fn.__name__} relies on a experimental feature in the api. This means that the interface could change."
                " Set `enable_experimental=True` in the client to enable use of experimental functions."
            )
        return fn(self, *args, **kwargs)

    return wrapper
