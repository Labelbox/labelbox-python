from enum import Enum
from typing import List, Union


class IdType(str, Enum):
    DataRowId = "UID"
    GlobalKey = "GLOBAL_KEY"


class Identifiables:

    def __init__(self, iterable, id_type: IdType):
        self._iterable = iterable
        self._index = 0
        self._id_type = id_type

    def __iter__(self):
        return iter(self._iterable)


class UniqueIds(Identifiables):

    def __init__(self, iterable: List[str]):
        super().__init__(iterable, IdType.DataRowId)


class GlobalKeys(Identifiables):

    def __init__(self, iterable: List[str]):
        super().__init__(iterable, IdType.GlobalKey)


DataRowIdentifiers = Union[UniqueIds, GlobalKeys]
