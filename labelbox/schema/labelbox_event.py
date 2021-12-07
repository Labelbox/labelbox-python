from typing import Union, Dict, Any

from labelbox.schema.project import Project
from labelbox.schema.user import User


class LabelboxEvent:

    def __init__(self, id, created_at, type, resource, actor):
        self.id: int = id
        self.created_at: str = created_at
        self.type: str = type
        self.resource: Union[Project, User] = resource
        self.actor: User = actor

    @classmethod
    def from_dict(cls, dictionary: Dict[str, Any]):
        return cls(id=dictionary['id'],
                   created_at=dictionary['created_at'],
                   type=dictionary['type'],
                   resource=dictionary['resource'],
                   actor=dictionary['actor'])