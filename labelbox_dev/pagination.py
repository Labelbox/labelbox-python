from abc import abstractmethod
from collections import deque, Iterator
from typing import Dict, List, Type

from labelbox_dev.session import Session
from labelbox_dev.entity import Entity

CURSOR_KEY = 'cursor'
DATA_KEY = 'data'
LIMIT_KEY = 'limit'
NEXT_CURSOR_KEY = 'next'
DEFAULT_IDENTIFIER_KEY = 'ids'
DEFAULT_LIMIT = 100


class BasePaginator(Iterator):
    """
    Loops over pages of a HTTP GET endpoint to retrieve all items
    """

    def __init__(self, resource, entity_class, params, limit):
        self.resource: str = resource
        self.entity_class: Type[Entity] = entity_class
        self.limit: int = limit
        self.params: Dict = params if params else {}
        self._is_last_page: bool = False
        self._entities_from_last_page = deque()
        self._session = Session

    def __iter__(self):
        return self

    @abstractmethod
    def get_next_page() -> List[Dict]:
        """
        Gets next page and sets _is_last_page = True when done
        """
        ...

    def deserialize_entity(self, entity: Dict) -> Entity:
        """Creates an entity object from JSON object. This can be overridden in a subclass to change instantiation behaviour."""
        return self.entity_class(entity)

    def __next__(self) -> Entity:
        if self._entities_from_last_page:
            return self._entities_from_last_page.popleft()
        elif self._is_last_page:  # Order of these conditions is important
            raise StopIteration
        else:
            page = self.get_next_page()
            for entity in page:
                self._entities_from_last_page.append(
                    self.deserialize_entity(entity))
            return next(self)


class IdentifierPaginator(BasePaginator):
    """
    Fetches entities by a list of identifiers by breaking them into pages of size `limit`.

    Args:
        resource: HTTP endpoint path
        entity_class: Subclass of `Entity` to cast objects from endpoint into
        identifiers: List of `ids`, `global_keys` or other keys to fetch entities by
        params: Additional query parameters to pass to the HTTP endpoint
        limit: Size of pages
        identifiers_key: Name of identifier field e.g. `ids` or `global_keys`
    """

    def __init__(self,
                 resource,
                 entity_class,
                 identifiers,
                 params=None,
                 limit=DEFAULT_LIMIT,
                 identifiers_key=DEFAULT_IDENTIFIER_KEY):
        self.resource: str = resource
        self.entity_class: Type[Entity] = entity_class
        self.identifiers: List[str] = identifiers
        self.identifiers_key: str = identifiers_key
        self.limit: int = limit
        self._current_idx = 0
        super().__init__(resource, entity_class, params, limit)

    def get_next_page(self):
        end_idx = self._current_idx + self.limit
        identifiers_for_page = self.identifiers[self._current_idx:end_idx]
        self._current_idx += self.limit
        if self._current_idx >= len(self.identifiers):
            self._is_last_page = True

        identifiers_str = ','.join(identifiers_for_page)
        params = self.params.copy()
        params.update({self.identifiers_key: identifiers_str})
        response = self._session.get_request(self.resource, params)
        return response


class CursorPaginator(BasePaginator):
    """
    Loops over all pages of an HTTP endpoint and returns entities. 

    Args:
        resource: HTTP endpoint path
        entity_class: Subclass of `Entity` to cast objects from endpoint into
        params: Additional query parameters to pass to the HTTP endpoint
        limit: Size of pages
    """

    def __init__(self,
                 resource,
                 entity_class,
                 params=None,
                 limit=DEFAULT_LIMIT):
        super().__init__(resource, entity_class, params, limit)
        self._cursor = None
        self.params.update({LIMIT_KEY: limit})

    def get_next_page(self):
        params = self.params.copy()
        if self._cursor:
            params.update({CURSOR_KEY: self._cursor})

        response = self._session.get_request(self.resource, params)

        try:
            self._cursor = response[NEXT_CURSOR_KEY]
            page = response[DATA_KEY]
        except KeyError:
            raise KeyError(
                f'Response from {self.resource} is missing `cursor` or `data`')

        if self._cursor is None:
            self._is_last_page = True

        return page
