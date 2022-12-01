from abc import ABC, abstractmethod
from typing import List
from labelbox_dev import utils


class Entity(ABC):

    def __init__(self, json):
        self.json = json
        self.id = json['id']

    def __repr__(self):
        return f"<{self.__class__.__name__} ID: {self.id}>"

    def __str__(self):
        return "<%s %s>" % (self.__class__.__name__, self.json)

    def from_json(self, json):
        self.json = utils.format_json_to_snake_case(json)