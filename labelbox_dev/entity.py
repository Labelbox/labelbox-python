import json

from labelbox_dev.utils import format_json_to_snake_case


class Entity:

    def __init__(self, json):
        self.json = json
        self.id = json['id']

    def __repr__(self):
        return f"<{self.__class__.__name__} ID: {self.id}>"

    def __str__(self):
        return "<%s %s>" % (self.__class__.__name__,
                            json.dumps(self.json, indent=4, default=str))

    def from_json(self, json):
        self.json = format_json_to_snake_case(json)
