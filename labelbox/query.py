from labelbox import utils


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
        tuple (query_string, id_param_name)
    """
    type_name = db_object_type.type_name()
    id_param_name = "%sID" % type_name.lower()
    query = "query Get%sPythonApi($%s: ID!) {%s(where: {id: $%s}) {%s}}" % (
        type_name,
        id_param_name,
        type_name.lower(),
        id_param_name,
        " ".join(field.graphql_name for field in db_object_type.fields()))
    return query, id_param_name


def get_all(db_object_type):
    """ Constructs a query that fetches all items of the given type. The
    resulting query is intended to be used for pagination, it contains
    two python-string int-placeholders (%d) for 'skip' and 'first'
    pagination parameters.

    Args:
        db_object_type (type): The object type being queried.
    Return:
        query_string
    """
    type_name = db_object_type.type_name()
    return """query Get%ssPyApi {%ss(where: {deleted: false}
                                     skip: %%d first: %%d) {%s} }""" % (
        type_name, type_name.lower(),
        " ".join(field.graphql_name for field in db_object_type.fields()))


def relationship(source, relationship, destination_type):
    """ Constructs a query that fetches all items from a -to-many
    relationship. To be used like:
        >>> project = ...
        >>> query_str, param_name = relationship(Project, "datasets", Dataset)
        >>> datasets = PaginatedCollection(
            client, query_str, {param_name: project.uid}, ["project", "datasets"],
            Dataset)

    The resulting query is intended to be used for pagination, it contains
    two python-string int-placeholders (%d) for 'skip' and 'first'
    pagination parameters.

    Args:
        source (DbObject): A database object.
        relationship (str): Name of the to-many relationship.
        destination_type (type): A DbObject subclass, type of the relationship
            objects.
    Return:
        tuple (query_string, id_parameter_name)
    """

    source_type_name = type(source).type_name()
    id_param_name = "%sID" % source_type_name
    query_string = """query %s($%s: ID!)
        {%s(where: {id: $%s}) {%s(skip: %%d first: %%d) {%s} } }""" % (
        source_type_name + utils.title_case(relationship) + "PyApi",
        id_param_name,
        utils.camel_case(source_type_name),
        id_param_name,
        relationship,
        " ".join(field.graphql_name for field in destination_type.fields()))

    return query_string, id_param_name
