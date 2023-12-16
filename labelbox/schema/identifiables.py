from enum import Enum
from typing import List, Union


class IdType(str, Enum):
    """
    The type of id used to identify a data row.
    
    Currently supported types are:
        - DataRowId: The id assigned to a data row by Labelbox.
        - GlobalKey: The id assigned to a data row by the user.
    """
    DataRowId = "ID"
    GlobalKey = "GKEY"


class Identifiables:

    def __init__(self, iterable, id_type: IdType):
        """
        Args:
            iterable: Iterable of ids (unique or global keys)
            id_type: The type of id used to identify a data row.
        """
        self._iterable = iterable
        self._index = 0
        self._id_type = id_type

    def __iter__(self):
        return iter(self._iterable)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self._iterable})"


class UniqueIds(Identifiables):
    """
    Represents a collection of unique, internally generated ids.
    """

    def __init__(self, iterable: List[str]):
        super().__init__(iterable, IdType.DataRowId)


class GlobalKeys(Identifiables):
    """
    Represents a collection of user generated ids.
    """

    def __init__(self, iterable: List[str]):
        super().__init__(iterable, IdType.GlobalKey)


DataRowIds = UniqueIds

DataRowIdentifiers = Union[UniqueIds, GlobalKeys]
