from itertools import chain

from labelbox import utils
from labelbox.exceptions import InvalidQueryError
from labelbox.filter import LogicalExpression, Comparison
from labelbox.schema import DbObject


# Size of a single page in a paginated query.
_PAGE_SIZE = 100


class PaginatedCollection:
    """ An iterable collection of database objects (Projects, Labels, etc...).
    Implements automatic (transparent to the user) paginated fetching during
    iteration. Intended for use by library internals and not by the end user.

    For a list of attributes see __init__(...) documentation. The params of
    __init__ map exactly to object attributes.
    """

    def __init__(self, client, query, params, dereferencing, obj_class):
        """ Creates a PaginatedCollection.
        Params:
            client (labelbox.Client): the client used for fetching data from DB.
            query (str): Base query used for pagination. It must contain two
                '%d' placeholders, the first for pagination 'skip' clause and
                the second for the 'first' clause.
            params (dict): Query parameters.
            dereferencing (iterable): An iterable of str defining the keypath
                that needs to be dereferenced in the query result in order to
                reach the paginated objects of interest.
            obj_class (type): The class of object to be instantiated with each
                dict containing db values.
        """
        self.client = client
        self.query = query
        self.params = params
        self.dereferencing = dereferencing
        self.obj_class = obj_class

        self._fetched_pages = 0
        self._fetched_all = False
        self._data = []

    def __iter__(self):
        self._data_ind = 0
        return self

    def __next__(self):
        if len(self._data) <= self._data_ind:
            if self._fetched_all:
                raise StopIteration()

            query = self.query % (self._fetched_pages * _PAGE_SIZE, _PAGE_SIZE)
            self._fetched_pages += 1

            results = self.client.execute(query, self.params)["data"]
            for deref in self.dereferencing:
                results = results[deref]

            page_data = [self.obj_class(self.client, result)
                         for result in results]
            self._data.extend(page_data)

            if len(page_data) < _PAGE_SIZE:
                self._fetched_all = True

            if len(page_data) == 0:
                raise StopIteration()

        rval = self._data[self._data_ind]
        self._data_ind += 1
        return rval


def get_single(db_object_type):
    """ Constructs a query that fetches a single item based on ID. The ID
    must be passed to query execution as a parameter like:
        >>> query_str, param_name = get_single(Project)
        >>> project = client.execute(query_str, {param_name: project_id})

    Args:
        db_object_type (type): The object type being queried.
    Return:
        tuple (query_str, id_param_name)
    """
    type_name = db_object_type.type_name()
    id_param_name = "%sID" % type_name.lower()
    query = "query Get%sPyApi($%s: ID!) {%s(where: {id: $%s}) {%s}}" % (
        type_name,
        id_param_name,
        type_name.lower(),
        id_param_name,
        " ".join(field.graphql_name for field in db_object_type.fields()))
    return query, id_param_name


# Maps comparison operations to the suffixes appended to the field
# name when generating a GraphQL query.
COMPARISON_TO_SUFFIX = {
    Comparison.Op.EQ: "",
    Comparison.Op.NE: "_not",
    Comparison.Op.LT: "_lt",
    Comparison.Op.GT: "_gt",
    Comparison.Op.LE: "_lte",
    Comparison.Op.LE: "_lte",
}


def format_where(where, params=None):
    """ Converts the given `where` clause into a query string. The clause
    can be a single `labelbox.filter.Comparison` or a complex
    `labelbox.filter.LogicalExpression` of arbitrary depth.

    Args:
        where (Comparison or LogicalExpression): The where clause
            used for filtering data.
    Return:
        (str, dict) tuple that contains the query string and a parameters
        dictionary. The dictionary now maps a {"name": (value, field)}, so
        the name of the parameter in the query string maps to a tuple of
        parameter value and `labelbox.schema.Field` object (which is
        necessary for obtaining the parameter type).
    """
    params = {}

    def recursion(node):
        if isinstance(node, Comparison):
            param_name = "param_%d" % len(params)
            params[param_name] = (node.value, node.field)
            return "{%s%s: $%s}" % (node.field.graphql_name,
                                    COMPARISON_TO_SUFFIX[node.op],
                                    param_name)

        assert(isinstance(node, LogicalExpression))

        if node.op == LogicalExpression.Op.NOT:
            return "{NOT: [%s]}" % recursion(node.first)

        return "{%s: [%s, %s]}" % (
            node.op.name.upper(), recursion(node.first), recursion(node.second))

    query_str = recursion(where)
    return query_str, params


def format_param_declaration(params):
    """ Formats the parameters dictionary (as returned by the
    `query.format_where` function) into a declaration of GraphQL function
    parameters.

    Args:
        params (dict): Parameter dictionary, as returned by the
            `query.format_where` function.
    Return:
        str, the declaration of query parameters.
    """
    params = ((key, field.field_type.name) for key, (_, field)
              in sorted(params.items()))
    return "(" + ", ".join("$%s: %s!" % pair for pair in params) + ")"


def fields(where):
    """ Returns a generator that yields all the Field objects from
    a where clause.

    Args:
        where (LogicalExpression, Comparison or None): The where
            clause used for filtering in a query.
    Return:
        See above.
    """
    if isinstance(where, LogicalExpression):
        for f in chain(fields(where.first), fields(where.second)):
            yield f
    elif isinstance(where, Comparison):
        yield where.field


def logical_ops(where):
    """ Returns a generator that yields all the logical operator
    type objects (`LogicalExpression.Op` instances) from a where
    clause.

    Args:
        where (LogicalExpression, Comparison or None): The where
            clause used for filtering in a query.
    Return:
        See above.
    """
    if isinstance(where, LogicalExpression):
        yield where.op
        for f in chain(logical_ops(where.first), logical_ops(where.second)):
            yield f

def check_where_clause(db_object_type, where):
    where_fields = list(fields(where))
    invalid_fields = set(where_fields) - set(db_object_type.fields())
    if invalid_fields:
        raise InvalidQueryError("Where clause contains fields '%r' which aren't "
                                "part of the '%s' DB object type" % (
                                    invalid_fields, db_object_type.type_name()))

    if len(set(where_fields)) != len(where_fields):
        raise InvalidQueryError("Where clause contains multiple comparisons for "
                                "the same field: %r." % where)

    if set(logical_ops(where)) not in (set(), {LogicalExpression.Op.AND}):
        raise InvalidQueryError("Currently only AND logical ops are allowed in "
                                "the where clause of a query.")


def get_all(db_object_type, where=None):
    """ Constructs a query that fetches all items of the given type. The
    resulting query is intended to be used for pagination, it contains
    two python-string int-placeholders (%d) for 'skip' and 'first'
    pagination parameters.

    Args:
        db_object_type (type): The object type being queried.
        where (Comparison, LogicalExpression or None): The `where` clause
            for filtering.
    Return:
        (str, dict) tuple that is the query string and parameters.
    """
    check_where_clause(db_object_type, where)

    deleted_filter = db_object_type.deleted == False
    where = deleted_filter if where is None else (where & deleted_filter)
    where_query_str, params = format_where(where)
    param_declaration_str = format_param_declaration(params)

    type_name = db_object_type.type_name()
    query_str = "query Get%ssPyApi%s {%ss(where: %s skip: %%d first: %%d) {%s} }" % (
        type_name,
        param_declaration_str,
        type_name.lower(),
        where_query_str,
        " ".join(field.graphql_name for field in db_object_type.fields()))

    return query_str, {name: value for name, (value, _) in params.items()}


def relationship(source, relationship, destination_type, where=None):
    """ Constructs a query that fetches all items from a -to-many
    relationship. To be used like:
        >>> project = ...
        >>> query_str, params = relationship(Project, "datasets", Dataset)
        >>> datasets = PaginatedCollection(
            client, query_str, params, ["project", "datasets"],
            Dataset)

    The resulting query is intended to be used for pagination, it contains
    two python-string int-placeholders (%d) for 'skip' and 'first'
    pagination parameters.

    Args:
        source (DbObject): A database object.
        relationship (str): Name of the to-many relationship.
        destination_type (type): A DbObject subclass, type of the relationship
            objects.
        where (Comparison, LogicalExpression or None): The `where` clause
            for filtering.
    Return:
        (str, dict) tuple that is the query string and parameters.
    """
    check_where_clause(destination_type, where)
    source_type_name = type(source).type_name()

    # Update the destination filtering params with deleted=false
    deleted_filter = DbObject.deleted == False
    where = deleted_filter if where is None else (where & deleted_filter)

    # Prepare the destination filtering clause and params
    where_query_str, params = format_where(where)

    # Generate a name for the source filter and add it to params
    id_param_name = "%sID" % source_type_name
    params[id_param_name] = (source.uid, type(source).uid)

    query_str = """query %sPyApi%s
        {%s(where: {id: $%s}) {%s(where: %s skip: %%d first: %%d) {%s} } }""" % (
        source_type_name + utils.title_case(relationship),
        format_param_declaration(params),
        utils.camel_case(source_type_name),
        id_param_name,
        relationship,
        where_query_str,
        " ".join(field.graphql_name for field in destination_type.fields()))

    return query_str, {name: value for name, (value, _) in params.items()}
