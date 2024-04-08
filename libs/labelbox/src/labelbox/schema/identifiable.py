from abc import ABC
from typing import Union

from labelbox.schema.id_type import IdType


class Identifiable(ABC):
    """
    Base class for any object representing a unique identifier.
    """

    def __init__(self, key: str, id_type: str):
        self._key = key
        self._id_type = id_type

    @property
    def key(self):
        return self._key

    @property
    def id_type(self):
        return self._id_type

    def __eq__(self, other):
        return other.key == self.key and other.id_type == self.id_type

    def __hash__(self):
        return hash((self.key, self.id_type))

    def __str__(self):
        return f"{self.id_type}:{self.key}"


class UniqueId(Identifiable):
    """
    Represents a unique, internally generated id.
    """

    def __init__(self, key: str):
        super().__init__(key, IdType.DataRowId)


class GlobalKey(Identifiable):
    """
    Represents a user generated id.
    """

    def __init__(self, key: str):
        super().__init__(key, IdType.GlobalKey)


DataRowIdentifier = Union[UniqueId, GlobalKey]
