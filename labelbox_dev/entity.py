from abc import ABC, abstractmethod
from typing import List


class Entity(ABC):

    def __init__(self, json):
        self.json = json
        self.id = json['id']

    def __repr__(self):
        return f"<{self.__class__.__name__} ID: {self.id}>"

    def __str__(self):
        return "<%s %s>" % (self.__class__.__name__, self.json)

    @abstractmethod
    def from_json(self, json):
        raise NotImplementedError("Must implement the abstract method")
