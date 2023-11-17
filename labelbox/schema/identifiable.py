from abc import ABC, abstractmethod
from enum import Enum
from typing import List, Union


class IdType(str, Enum):
    DataRowId = "UID"
    GlobalKey = "GLOBAL_KEY"


class Identifiable(ABC):

    def __init__(self, keys: Union[str, List[str]], id_type: IdType):
        self._keys = keys
        if isinstance(keys, str):
            self._keys = [keys]
        self._id_type = id_type

    @property
    def keys(self):
        return self._keys

    @keys.setter
    def keys(self, keys):
        self._keys = keys
        if isinstance(keys, str):
            self._keys = [keys]

    @classmethod
    @abstractmethod
    def strings_to_identifiable(cls, keys: Union[str, List[str]]):
        pass

    def __eq__(self, other):
        return other.keys == self.keys

    def __hash__(self):
        hash(self.keys)

    def __str__(self):
        return self.keys.__str__()


class UniqueIds(Identifiable):

    @classmethod
    def strings_to_identifiable(cls, keys: Union[str, List[str]]):
        return cls(keys)

    def __init__(self, keys: Union[str, List[str]]):
        super().__init__(keys, IdType.DataRowId)


class GlobalKeys(Identifiable):

    @classmethod
    def strings_to_identifiable(cls, keys: Union[str, List[str]]):
        return cls(keys)

    def __init__(self, keys: Union[str, List[str]]):
        super().__init__(keys, IdType.GlobalKey)


DefaultIdentifiable = UniqueIds
DataRowIdentifiers = Union[UniqueIds, GlobalKeys]