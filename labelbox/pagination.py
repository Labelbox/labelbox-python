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

        Args:
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
        self._data_ind = 0

    def __iter__(self):
        self._data_ind = 0
        return self

    def __next__(self):
        if len(self._data) <= self._data_ind:
            if self._fetched_all:
                raise StopIteration()

            query = self.query % (self._fetched_pages * _PAGE_SIZE, _PAGE_SIZE)
            self._fetched_pages += 1

            results = self.client.execute(query, self.params)
            for deref in self.dereferencing:
                results = results[deref]

            page_data = [
                self.obj_class(self.client, result) for result in results
            ]
            self._data.extend(page_data)

            if len(page_data) < _PAGE_SIZE:
                self._fetched_all = True

            if len(page_data) == 0:
                raise StopIteration()

        rval = self._data[self._data_ind]
        self._data_ind += 1
        return rval
