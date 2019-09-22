from itertools import chain

from labelbox import utils
from labelbox.exceptions import InvalidQueryError, InvalidAttributeError
from labelbox.filter import LogicalExpression, Comparison
from labelbox.schema import DbObject, Field, Relationship


# Maps comparison operations to the suffixes appended to the field
# name when generating a GraphQL query.
COMPARISON_TO_SUFFIX = {
    Comparison.Op.EQ: "",
    Comparison.Op.NE: "_not",
    Comparison.Op.LT: "_lt",
    Comparison.Op.GT: "_gt",
    Comparison.Op.LE: "_lte",
    Comparison.Op.GE: "_gte",
}


def format_param_declaration(params):
    """ Formats the parameters dictionary into a declaration of GraphQL
    query parameters.

    Args:
        params (dict): keys are query param names and values are
            (value, (field|relationship)) tuples.
    Return:
        str, the declaration of query parameters.
    """
    if not params:
        return ""

    def attr_type(attr):
        if isinstance(attr, Field):
            return attr.field_type.name
        else:
            return Field.Type.ID.name

    return "(" + ", ".join("$%s: %s!" % (param, attr_type(attr))
                           for param, (_, attr) in params.items()) + ")"


class Query:
    """ A data structure used during the construction of a query. Supports
    subquery (also Query object) nesting for relationship. """

    def __init__(self, what, subquery, where=None, paginate=False,
                 order_by=None):
        """ Initializer.
        Args:
            what (str): What is being queried. Typically an object type in
                singular or plural (i.e. "project" or "projects").
            subquery (Query or type): Either a Query object that is formatted
                recursively or a DbObject subtype in which case all it's public
                fields are retrieved by the query.
            where (None, Comparison or LogicalExpression): the filtering clause.
            paginate (bool): If the "%skip %first" pagination substring should
                be added to the query. Used for collection pagination in combination
                with PaginatedCollection.
            order_by (tuple): A tuple consisting of (Field, Field.Order) indicating
                how the query should sort the collection.
        """
        self.what = what
        self.subquery = subquery
        self.paginate = paginate
        self.where = where
        self.order_by = order_by

    def format_subquery(self):
        """ Formats the subquery (a Query or DbObject subtype). """
        if isinstance(self.subquery, Query):
            return self.subquery.format()
        elif issubclass(self.subquery, DbObject):
            return " ".join(f.graphql_name for f in self.subquery.fields()), {}
        else:
            raise MalformedQueryException()

    def format_clauses(self, params):
        """ Formats the where, order_by and pagination clauses.
        Args:
            params (dict): The current parameter dictionary.
        """

        def format_where(node):
            """ Helper that resursively constructs a where clause from a
            LogicalExpression tree (leaf nodes are Comparisons). """
            assert isinstance(node, (Comparison, LogicalExpression))
            if isinstance(node, Comparison):
                param_name = "param_%d" % len(params)
                params[param_name] = (node.value, node.field)
                return "{%s%s: $%s}" % (node.field.graphql_name,
                                        COMPARISON_TO_SUFFIX[node.op],
                                        param_name)
            if node.op == LogicalExpression.Op.NOT:
                return "{NOT: [%s]}" % format_where(node.first)

            return "{%s: [%s, %s]}" % (
                node.op.name.upper(), format_where(node.first),
                format_where(node.second))

        paginate = "skip: %d first: %d" if self.paginate else ""

        where = "where: %s" % format_where(self.where) if self.where else ""

        if self.order_by:
            order_by = "orderBy: %s_%s" % (
                self.order_by[0].graphql_name, self.order_by[1].name.upper())
        else:
            order_by = ""

        clauses = " ".join(filter(None, (where, paginate, order_by)))
        return "(" + clauses + ")" if clauses else ""


    def format(self):
        """ Formats the full query but without "query" prefix, query name
        and parameter declaration.
        Return:
            (str, dict) tuple. str is the query and dict maps parameter
            names to (value, field) tuples.
        """
        subquery, params = self.format_subquery()
        clauses = self.format_clauses(params)
        query = "%s%s{%s}" % (self.what, clauses, subquery)
        return query, params

    def format_top(self, name):
        """ Formats the full query including "query" prefix, query name
        and parameter declaration. The result of this function can be
        sent to the Client object for execution.

        Args:
            name (str): Query name, without the "PyApi" suffix, it's appended
                automatically by this method.
        Return:
            (str, dict) tuple. str is the full query and dict maps parameter
                names to parameter values.
        """
        query, params = self.format()
        param_declaration = format_param_declaration(params)
        query = "query %sPyApi%s{%s}" % (name, param_declaration, query)
        return query, {param: value for param, (value, _) in params.items()}


def get_single(db_object_type, uid):
    """ Constructs the query and params dict for obtaining a single object. Either
    on ID, or without params.
    Args:
        db_object_type (type): A DbObject subtype being obtained.
        uid (str): The ID of the sought object. It can be None, which is legal for
            DB types that have a default object being returned (User and
            Organization).
    """
    type_name = db_object_type.type_name()
    where = db_object_type.uid == uid if uid else None
    return Query(utils.camel_case(type_name), db_object_type, where).format_top(
        "Get" + type_name)


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
        raise InvalidAttributeError(db_object_type, invalid_fields)

    if len(set(where_fields)) != len(where_fields):
        raise InvalidQueryError("Where clause contains multiple comparisons for "
                                "the same field: %r." % where)

    if set(logical_ops(where)) not in (set(), {LogicalExpression.Op.AND}):
        raise InvalidQueryError("Currently only AND logical ops are allowed in "
                                "the where clause of a query.")


def check_order_by_clause(db_object_type, order_by):
    if order_by is not None:
        field, _ = order_by
        if field not in db_object_type.fields():
            raise InvalidAttributeError(db_object_type, field)


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
    type_name = db_object_type.type_name()
    query = Query(utils.camel_case(type_name) + "s", db_object_type, where, True)
    return query.format_top("Get" + type_name + "s")


def relationship(source, relationship, destination_type, to_many,
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
        relationship (Relationship): The relationship object.
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
    check_order_by_clause(destination_type, order_by)
    subquery = Query(relationship.graphql_name, destination_type,
                     where, to_many, order_by)
    source_type_name = type(source).type_name()
    query = Query(utils.camel_case(source_type_name), subquery,
                  type(source).uid == source.uid)
    return query.format_top(
        "Get" + source_type_name + utils.title_case(relationship.graphql_name))


def create(db_object_type, data):
    """ Generats a query and parameters for creating a new DB object.

    Args:
        db_object_type (type): A DbObject subtype indicating which kind of
            DB object needs to be created.
        data (dict): A dict that maps Fields and Relationships to values, new
            object data.
    Return:
        (query_string, parameters)
    """
    type_name = db_object_type.type_name()

    def format_param_value(attribute, param):
        if isinstance(attribute, Field):
            return "%s: $%s" % (attribute.graphql_name, param)
        else:
            return "%s: {connect: {id: $%s}}" % (
                utils.camel_case(attribute.graphql_name), param)

    # Convert data to params
    params = {field.graphql_name: (value, field) for field, value in data.items()}

    query_str = """mutation Create%sPyApi%s{create%s(data: {%s}) {%s}} """ % (
        type_name,
        format_param_declaration(params),
        type_name,
        " ".join(format_param_value(attribute, param)
                 for param, (_, attribute) in params.items()),
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


def set_labeling_parameter_overrides(project, data):
    """ Constructs a query for setting labeling parameter overrides.
    Args:
        project (Project): The project to set param overrides for.
            data (iterable): An iterable of tuples. Each tuple must contain
                (DataRow, priority, numberOfLabels) for the new override.
    Return:
        (query_string, query_parameters)
    """
    data_str = ",\n".join(
        "{dataRow: {id: \"%s\"}, priority: %d, numLabels: %d }" % (
            data_row.uid, priority, num_labels)
        for data_row, priority, num_labels in data)
    query_str = """mutation setLabelingParameterOverridesPyApi {
        project(where: { id: "%s" }) {
            setLabelingParameterOverrides(data: [%s]) { success } } } """ % (
                project.uid, data_str)
    return query_str, {}


def unset_labeling_parameter_overrides(project, data_rows):
    """ Constructs a query for unsetting labeling parameter overrides.
    Args:
        project (Project): The project to set param overrides for.
        data_rows (iterable): An iterable of DataRow objects
            for which the to set as parameter overrides.
    Return:
        (query_string, query_parameters)
    """
    data_str = ",\n".join("{dataRowId: \"%s\"}" % data_row.uid
                          for data_row in data_rows)
    query_str = """mutation unsetLabelingParameterOverridesPyApi {
        project(where: { id: "%s" }) {
            unsetLabelingParameterOverrides(data: [%s]) { success } } } """ % (
                project.uid, data_str)
    return query_str, {}


def create_metadata(asset_type, meta_type, meta_value, data_row_id):
    meta_type_param = "meta_type"
    meta_value_param = "meta_value"
    data_row_id_param = "data_row_id"
    query_str = """mutation CreateAssetMetadataPyApi(
        $%s: MetadataType!, $%s: String!, $%s: ID!) {
        createAssetMetadata(data: {
            metaType: $%s metaValue: $%s dataRowId: $%s}) {%s}} """ % (
        meta_type_param, meta_value_param, data_row_id_param,
        meta_type_param, meta_value_param, data_row_id_param,
        " ".join(field.graphql_name for field in asset_type.fields()))
    return query_str, {meta_type_param: meta_type,
                       meta_value_param: meta_value,
                       data_row_id_param: data_row_id}


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
    """
    type_name = db_object.type_name()
    id_param = "%sId" % type_name
    values_str = " ".join("%s: $%s" % (field.graphql_name, field.graphql_name)
                          for field, _ in values.items())
    params = {field.graphql_name: (value, field) for field, value
              in values.items()}
    params[id_param] = (db_object.uid, DbObject.uid)

    query_str = """mutation update%sPyApi%s{update%s(
        where: {id: $%s} data: {%s}) {%s}} """ % (
        utils.title_case(type_name),
        format_param_declaration(params),
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


def export_labels():
    """ Returns the query and ID param for exporting a Project's
    labels.
    Return:
        (query_string, id_param_name)
    """
    id_param = "projectId"
    query_str = """mutation GetLabelExportUrlPyApi($%s: ID!) {exportLabels(data:{
        projectId: $%s } ) {
        downloadUrl createdAt shouldPoll } }
    """ %  (id_param, id_param)
    return (query_str, id_param)


def bulk_delete(db_objects, use_where_clause):
    """ Generates a query that bulk-deletes the given `db_objects` from the
    DB.

    Args:
        db_objects (list): A list of DB objects of the same type.
        use_where_clause (bool): If the object IDs should be passed to the
            mutation in a `where` clause or directly as a mutation value.
    """
    db_object_type = type(db_objects[0])
    type_name = db_object_type.type_name()
    if use_where_clause:
        query_str = "mutation delete%ssPyApi{delete%ss(where: {%sIds: [%s]}){id}}"
    else:
        query_str = "mutation delete%ssPyApi{delete%ss(%sIds: [%s]){id}}"
    query_str = query_str % (
        utils.title_case(type_name),
        utils.title_case(type_name),
        utils.camel_case(type_name),
        ", ".join('"%s"' % db_object.uid for db_object in db_objects)
    )
    return query_str, {}
