from typing import Union

from pydantic import BaseModel
from labelbox.schema.project import Project
from labelbox.schema.user import User


class LabelboxEvent:

    def __init__(self):
        self.id: int = 0
        self.created_at: str
        self.type: str
        self.resource: Union[Project, User]
        self.actor: User

    @classmethod
    def from_event(cls, dictionary: dict) -> 'LabelboxEvent':
        return cls(id=dictionary['id'],
                   created_at=dictionary['created_At'],
                   type=dictionary['type'],
                   resource=dictionary['resource'],
                   actor=dictionary['actor'])
