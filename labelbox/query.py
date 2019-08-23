from enum import Enum

from labelbox import utils


# Size of a single page in a paginated query.
_PAGE_SIZE = 100

"""
Database query construction and execution functions and
supporting classes. These should only be used by the library
internals and not by the libraray user.
"""

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
            graphql_name = utils.snake_to_camel(name)
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

    def __repr__(self):
        #TODO ensure that object has "uid" attribute, or check
        return "<%s ID: %s>" % (type(self).__name__.split(".")[-1], self.uid)

    def __str__(self):
        # TODO discuss exact __repr__ and __str__ representations
        attribute_values = {field.name: getattr(self, field.name)
                            for field in type(self).fields()}
        return "<%s %s>" % (type(self).__name__.split(".")[-1],
                                attribute_values)


class PaginatedCollection:
    """ An iterable collection of database objects (Projects, Labels, etc...).
    Implements automatic (transparent to the user) paginated fetching during
    iteration. Intended for use by library internals and not by the end user.

    For a list of attributes see __init__(...) documentation. The params of
    __init__ map exactly to object attributes.
    """

    def __init__(self, client, query, dereferencing, obj_class):
        """ Creates a PaginatedCollection.
        Params:
            client (labelbox.Client): the client used for fetching data from DB.
            query (str): Base query used for pagination. It must contain two
                '%d' placeholders, the first for pagination 'skip' clause and
                the second for the 'first' clause.
            dereferencing (iterable): An iterable of str defining the keypath
                that needs to be dereferenced in the query result in order to
                reach the paginated objects of interest.
            obj_class (type): The class of object to be instantiated with each
                dict containing db values.
        """
        self.client = client
        self.query = query
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

            results = self.client.execute(query)["data"]
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
