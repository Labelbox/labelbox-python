from typing import Annotated, List
from pydantic import Field


from dataclasses import dataclass

from typing import Any, Dict, List


@dataclass
class FeatureSchemaAttribute:
    attributeName: str
    attributeValue: str

    def asdict(self):
        return {
            "attributeName": self.attributeName,
            "attributeValue": self.attributeValue,
        }

    @classmethod
    def from_dict(cls, dictionary: Dict[str, Any]) -> "FeatureSchemaAttribute":
        return cls(
            attributeName=dictionary["attributeName"],
            attributeValue=dictionary["attributeValue"],
        )


FeatureSchemaId = Annotated[str, Field(min_length=25, max_length=25)]
SchemaId = Annotated[str, Field(min_length=25, max_length=25)]
FeatureSchemaAttributes = Annotated[
    List[FeatureSchemaAttribute], Field(default_factory=list)
]
