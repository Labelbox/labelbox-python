from abc import ABC
from enum import Enum
from typing import List, Union
from typing_extensions import TypeAlias


class IdType(str, Enum):
    DataRowId = "DATA_ROW_ID"
    GlobalKey = "GLOBAL_KEY"


class Identifiable(ABC):

    def __init__(self, keys: Union[str, List[str]]):
        self._keys = keys
        if isinstance(keys, str):
            self.keys = [keys]
        self._id_type = IdType.DataRowId

    @property
    def keys(self):
        return self._keys

    @keys.setter
    def keys(self, keys):
        self._keys = keys
        if isinstance(keys, str):
            self.keys = [keys]

    @property
    def id_type(self):
        return self._id_type

    def __eq__(self, other):
        return other.keys == self.keys

    def __hash__(self):
        hash(self.keys)

    def __str__(self):
        return self.keys.__str__()


class UniqueIds(Identifiable):

    def __init__(self, keys: Union[str, List[str]]):
        super().__init__(keys)
        self._id_type = IdType.DataRowId


class GlobalKeys(Identifiable):

    def __init__(self, keys: Union[str, List[str]]):
        super().__init__(keys)
        self._id_type = IdType.GlobalKey


DefaultIdentifiable: TypeAlias = UniqueIds
DataRowIdentifiers: TypeAlias = Union[UniqueIds, GlobalKeys]


def strings_to_identifiable(keys: Union[str, List[str]]) -> DefaultIdentifiable:
    return DefaultIdentifiable(keys)
