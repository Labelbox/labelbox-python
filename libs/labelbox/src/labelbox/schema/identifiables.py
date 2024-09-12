from typing import List, Union

from labelbox.schema.id_type import IdType


class Identifiables:
    def __init__(self, iterable, id_type: str):
        """
        Args:
            iterable: Iterable of ids (unique or global keys)
            id_type: The type of id used to identify a data row.
        """
        self._iterable = iterable
        self._id_type = id_type

    @property
    def id_type(self):
        return self._id_type

    def __iter__(self):
        return iter(self._iterable)

    def __getitem__(self, index):
        if isinstance(index, slice):
            ids = self._iterable[index]
            return self.__class__(ids)  # type: ignore
        return self._iterable[index]

    def __len__(self):
        return len(self._iterable)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self._iterable})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Identifiables):
            return False
        return (
            self._iterable == other._iterable
            and self._id_type == other._id_type
        )


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
