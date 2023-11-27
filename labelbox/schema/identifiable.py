from abc import ABC, abstractmethod
from typing import List, Union


class Identifiable(ABC):
    """
    Base class for any object representing a unique identifier.
    """

    def __init__(self, key: str):
        self._key = key

    @property
    def key(self):
        return self.key

    def __eq__(self, other):
        return other.key == self.key

    def __hash__(self):
        hash(self.key)

    def __str__(self):
        return self.key.__str__()


class UniqueId(Identifiable):
    """
    Represents a unique, internally generated id.
    """
    pass


class GlobalKey(Identifiable):
    """
    Represents a user generated id.
    """
    pass
