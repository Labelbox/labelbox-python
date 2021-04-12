# Size of a single page in a paginated query.
_PAGE_SIZE = 100


class PaginatedCollection:
    """ An iterable collection of database objects (Projects, Labels, etc...).

    Implements automatic (transparent to the user) paginated fetching during
    iteration. Intended for use by library internals and not by the end user.
    For a list of attributes see __init__(...) documentation. The params of
    __init__ map exactly to object attributes.
    """

    def __init__(self,
                 client,
                 query,
                 params,
                 dereferencing,
                 obj_class,
                 cursor_path=None,
                 experimental=False):
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
            cursor_path: If not None, this is used to find the cursor
            experimental: Used to call experimental endpoints
        """
        self.client = client
        self.query = query
        self.params = params
        self.dereferencing = dereferencing
        self.obj_class = obj_class
        self.experimental = experimental

        self._fetched_pages = 0
        self._fetched_all = False
        self._data = []
        self._data_ind = 0
        self.next_cursor = None
        self.cursor_path = cursor_path

    def __iter__(self):
        self._data_ind = 0
        return self

    def get_page_data(self, results):
        for deref in self.dereferencing:
            results = results[deref]

        return [self.obj_class(self.client, result) for result in results]

    def get_next_cursor(self, results):
        for path in self.cursor_path:
            results = results[path]
        return results

    def __next__(self):
        if len(self._data) <= self._data_ind:
            if self._fetched_all:
                raise StopIteration()

            if self.cursor_path:
                # Cursor Pagination
                self.params.update({
                    'from': self.next_cursor,
                    'first': _PAGE_SIZE
                })
                query = self.query
            else:
                # Offset Pagination
                query = self.query % (self._fetched_pages * _PAGE_SIZE,
                                      _PAGE_SIZE)

            self._fetched_pages += 1

            results = self.client.execute(query,
                                          self.params,
                                          experimental=self.experimental)
            page_data = self.get_page_data(results)
            self._data.extend(page_data)

            if len(page_data) < _PAGE_SIZE:
                self._fetched_all = True

            if len(page_data) == 0:
                raise StopIteration()

            if self.cursor_path:
                self.next_cursor = self.get_next_cursor(results)
                if self.next_cursor is None:
                    self._fetched_all = True

        rval = self._data[self._data_ind]
        self._data_ind += 1
        return rval
