# Size of a single page in a paginated query.
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional, Tuple, Type, Union

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from labelbox import Client
    from labelbox.orm.db_object import DbObject

_PAGE_SIZE = 100


class PaginatedCollection:
    """ An iterable collection of database objects (Projects, Labels, etc...).

    Implements automatic (transparent to the user) paginated fetching during
    iteration. Intended for use by library internals and not by the end user.
    For a list of attributes see __init__(...) documentation. The params of
    __init__ map exactly to object attributes.
    """

    def __init__(self,
                 client: "Client",
                 query: str,
                 params: Dict[str, str],
                 dereferencing: Union[List[str], Dict[str, Any]],
                 obj_class: Union[Type["DbObject"], Callable[[Any, Any], Any]],
                 cursor_path: Optional[List[str]] = None,
                 experimental: bool = False):
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
        self._fetched_all = False
        self._data: List[Dict[str, Any]] = []
        self._data_ind = 0

        pagination_kwargs = {
            'client': client,
            'obj_class': obj_class,
            'dereferencing': dereferencing,
            'experimental': experimental,
            'query': query,
            'params': params
        }

        self.paginator = _CursorPagination(
            cursor_path, **
            pagination_kwargs) if cursor_path else _OffsetPagination(
                **pagination_kwargs)

    def __iter__(self):
        self._data_ind = 0
        return self

    def __next__(self):
        if len(self._data) <= self._data_ind:
            if self._fetched_all:
                raise StopIteration()

            page_data, self._fetched_all = self.paginator.get_next_page()
            self._data.extend(page_data)
            if len(page_data) == 0:
                raise StopIteration()

        rval = self._data[self._data_ind]
        self._data_ind += 1
        return rval


class _Pagination(ABC):

    def __init__(self, client: "Client", obj_class: Type["DbObject"],
                 dereferencing: Dict[str, Any], query: str,
                 params: Dict[str, Any], experimental: bool):
        self.client = client
        self.obj_class = obj_class
        self.dereferencing = dereferencing
        self.experimental = experimental
        self.query = query
        self.params = params

    def get_page_data(self, results: Dict[str, Any]) -> List["DbObject"]:
        for deref in self.dereferencing:
            results = results[deref]

        return [self.obj_class(self.client, result) for result in results]

    @abstractmethod
    def get_next_page(self) -> Tuple[Dict[str, Any], bool]:
        ...


class _CursorPagination(_Pagination):

    def __init__(self, cursor_path: List[str], *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cursor_path = cursor_path
        self.next_cursor: Optional[Any] = None

    def increment_page(self, results: Dict[str, Any]):
        for path in self.cursor_path:
            results = results[path]
        self.next_cursor = results

    def fetched_all(self) -> bool:
        return not self.next_cursor

    def fetch_results(self) -> Dict[str, Any]:
        self.params.update({'from': self.next_cursor, 'first': _PAGE_SIZE})
        return self.client.execute(self.query,
                                   self.params,
                                   experimental=self.experimental)

    def get_next_page(self):
        results = self.fetch_results()
        page_data = self.get_page_data(results)
        self.increment_page(results)
        done = self.fetched_all()
        return page_data, done


class _OffsetPagination(_Pagination):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._fetched_pages = 0

    def increment_page(self):
        self._fetched_pages += 1

    def fetched_all(self, n_items: int) -> bool:
        return n_items < _PAGE_SIZE

    def fetch_results(self) -> Dict[str, Any]:
        query = self.query % (self._fetched_pages * _PAGE_SIZE, _PAGE_SIZE)
        return self.client.execute(query,
                                   self.params,
                                   experimental=self.experimental)

    def get_next_page(self):
        results = self.fetch_results()
        page_data = self.get_page_data(results)
        self.increment_page()
        done = self.fetched_all(len(page_data))
        return page_data, done
