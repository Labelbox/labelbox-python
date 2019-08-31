from itertools import chain

from labelbox import utils
from labelbox.exceptions import InvalidQueryError, InvalidFieldError
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


def get_user(user_db_type):
    return "query GetUserPyApi {%s {%s}}" % (
        utils.camel_case(user_db_type.type_name()),
        " ".join(field.graphql_name for field in user_db_type.fields()))


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


def format_where(where):
    """ Converts the given `where` clause into a query string. The clause
    can be a single `labelbox.filter.Comparison` or a complex
    `labelbox.filter.LogicalExpression` of arbitrary depth.

    Args:
        where (None, Comparison or LogicalExpression): The where clause
            used for filtering data.
    Return:
        (str, dict) tuple that contains the query string and a parameters
        dictionary. The dictionary now maps a {"name": (value, field)}, so
        the name of the parameter in the query string maps to a tuple of
        parameter value and `labelbox.schema.Field` object (which is
        necessary for obtaining the parameter type).
    """
    params = {}

    if where is None:
        return "{}", {}

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
            `query.format_where` function. dict keys are query param names
            and values are (value, field) tuples.
    Return:
        str, the declaration of query parameters.
    """
    params = ((key, field.field_type.name) for key, (_, field)
              in sorted(params.items()))
    return "(" + ", ".join("$%s: %s!" % pair for pair in params) + ")"


def format_order_by(order_by):
    """ Formats the order_by query clause.
    Args:
        order_by (None or (Field, Field.Order): The `order_by` clause for
            sorting results.
    Return:
        Order-by query substring in format " orderBy: <field_name>_<order>"
    """
    if order_by is None:
        return ""
    return " orderBy: %s_%s" % (order_by[0].graphql_name, order_by[1].name.upper())


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
    # The `deleted` field is a special case, ignore it.
    where_fields = [f for f in fields(where) if f != DbObject.deleted]
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


def get_all(db_object_type, where):
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

    where_query_str, params = format_where(where)
    param_declaration_str = format_param_declaration(params)

    type_name = db_object_type.type_name()
    query_str = "query Get%ssPyApi%s {%ss(where: %s skip: %%d first: %%d) {%s} }"
    query_str = query_str % (
        type_name,
        param_declaration_str,
        type_name.lower(),
        where_query_str,
        " ".join(field.graphql_name for field in db_object_type.fields()))

    return query_str, {name: value for name, (value, _) in params.items()}


def relationship(source, relationship_name, destination_type, to_many,
                 where, order_by):
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
        relationship_name (str): Name of the to-many relationship.
        destination_type (type): A DbObject subclass, type of the relationship
            objects.
        to_many (bool): Indicator if a paginated to-many query should be
            constructed or a non-paginated to-one query.
        where (Comparison, LogicalExpression or None): The `where` clause
            for filtering.
        order_by (None or (Field, Field.Order): The `order_by` clause for
            sorting results.
    Return:
        (str, dict) tuple that is the query string and parameters.
    """
    check_where_clause(destination_type, where)
    source_type_name = type(source).type_name()

    # Prepare the destination filtering clause and params
    where_query_str, params = format_where(where)

    # Generate a name for the source filter and add it to params
    id_param_name = "%sID" % source_type_name
    params[id_param_name] = (source.uid, type(source).uid)

    query_str = """query %sPyApi%s
        {%s(where: {id: $%s}) {%s(where: %s%s%s) {%s} } }""" % (
        source_type_name + utils.title_case(relationship_name),
        format_param_declaration(params),
        utils.camel_case(source_type_name),
        id_param_name,
        utils.camel_case(relationship_name),
        where_query_str,
        " skip: %d first: %d" if to_many else "",
        format_order_by(order_by),
        " ".join(field.graphql_name for field in destination_type.fields()))

    return query_str, {name: value for name, (value, _) in params.items()}


def create(db_object_type, data):
    """ Generats a query and parameters for creating a new DB object.

    Args:
        db_object_type (type): A DbObject subtype indicating which kind of
            DB object needs to be created.
        data (dict): A dict that maps Fields to values, new object data.
    Return:
        (query_string, parameters)
    """
    type_name = db_object_type.type_name()

    # Convert data to params
    params = {field.graphql_name: (value, field) for field, value in data.items()}

    query_str = """mutation Create%sPyApi%s{create%s(data: {%s}) {%s}} """ % (
        type_name,
        format_param_declaration(params),
        type_name,
        " ".join("%s: $%s" % (field.graphql_name, param)
                 for param, (_, field) in params.items()),
        " ".join(field.graphql_name for field in db_object_type.fields()))

    return query_str, {name: value for name, (value, _) in params.items()}


def create_data_rows(dataset_id, json_file_url):
    """ Generates the query and parameters dictionary for creating multiple
    DataRows for a Dataset.

    Args:
        dataset_id (str): ID of the Dataset object to create DataRows for.
        json_file_url (str): URL of the file containing row data.
    Return:
        (query_string, parameters_dict)
    """
    dataset_param = "dataSetId"
    url_param = "jsonURL"
    query_str = """mutation AppendRowsToDatasetPyApi(
                    $%s: ID!, $%s: String!){
          appendRowsToDataset(data:{datasetId: $%s, jsonFileUrl: $%s}
        ){ taskId accepted } } """ % (dataset_param, url_param, dataset_param,
                                      url_param)

    return query_str, {dataset_param: dataset_id, url_param: json_file_url}


def update_relationship(a, b, relationship_name, update):
    """ Updates the relationship in DB object `a` to connect or disconnect
    DB object `b`.

    Args:
        a (DbObject): The object being updated.
        b (DbObject): Object on the other side of the relationship.
        relationship_name (str): Relationship name.
        update (str): The type of update. Must be either `connect` or
            `disconnect`.
    Return:
        (query_string, query_parameters)
    """
    a_uid_param = utils.camel_case(type(a).type_name()) + "Id"
    b_uid_param = utils.camel_case(type(b).type_name()) + "Id"
    a_params = {DbObject.uid: a.uid}
    b_params = {DbObject.uid: b.uid}
    query_str = """mutation %s%sAnd%sPyApi%s{update%s(
        where: {id: $%s} data: {%s: {%s: {id: $%s}}}) {id}} """ % (
        utils.title_case(update),
        type(a).type_name(),
        type(b).type_name(),
        "($%s: ID!, $%s: ID!)" % (a_uid_param, b_uid_param),
        utils.title_case(type(a).type_name()),
        a_uid_param,
        utils.camel_case(relationship_name),
        update,
        b_uid_param)

    return query_str, {a_uid_param: a.uid, b_uid_param: b.uid}


def update_fields(db_object, values):
    """ Creates a query that updates `db_object` fields with the
    given values.

    Args:
        db_object (DbObject): The DB object being updated.
        values (dict): Maps Fields to new values. All Fields
            must be legit fields in `db_object`.
    Return:
        (query_string, query_parameters)
    Raise:
        InvalidFieldError: if there exists a key in `values`
            that's not a field in `db_object`.
    """
    invalid_fields = set(values) - set(db_object.fields())
    if invalid_fields:
        raise InvalidFieldError(type(db_object), invalid_fields)

    type_name = db_object.type_name()
    id_param = "%sId" % type_name
    values_str = " ".join("%s: $%s" % (field.graphql_name, field.name)
                          for field, _ in values.items())
    params = {field.graphql_name: (value, field) for field, value
              in values.items()}
    params[id_param] = (db_object.uid, DbObject.uid)

    query_str = """mutation update%sPyApi(%s){update%s(
        where: {id: $%s} data: {%s}) {%s}} """ % (
        utils.title_case(type_name),
        " ".join("$%s: %s!" % (name, field.field_type.name)
                 for name, (_, field) in params.items()),
        type_name,
        id_param,
        values_str,
        " ".join(field.graphql_name for field in db_object.fields()))

    return query_str, {name: value for name, (value, _) in params.items()}


def delete(db_object):
    """ Generates a query that deletes the given `db_object` from the DB.

    Args:
        db_object (DbObject): The DB object being deleted.
    """
    id_param = "%sId" % db_object.type_name()
    query_str = """mutation delete%sPyApi%s{update%s(
        where: {id: $%s} data: {deleted: true}) {id}} """ % (
            db_object.type_name(),
            "($%s: ID!)" % id_param,
            db_object.type_name(),
            id_param)

    return query_str, {id_param: db_object.uid}
