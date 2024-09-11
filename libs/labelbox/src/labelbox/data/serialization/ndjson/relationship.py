from typing import Union
from pydantic import BaseModel
from .base import NDAnnotation, DataRow
from ...annotation_types.data import ImageData, TextData
from ...annotation_types.relationship import RelationshipAnnotation
from ...annotation_types.relationship import Relationship
from .objects import NDObjectType
from .base import DataRow, _SubclassRegistryBase

SUPPORTED_ANNOTATIONS = NDObjectType


class _Relationship(BaseModel):
    source: str
    target: str
    type: str


class NDRelationship(NDAnnotation, _SubclassRegistryBase):
    relationship: _Relationship

    @staticmethod
    def to_common(
        annotation: "NDRelationship",
        source: SUPPORTED_ANNOTATIONS,
        target: SUPPORTED_ANNOTATIONS,
    ) -> RelationshipAnnotation:
        return RelationshipAnnotation(
            name=annotation.name,
            value=Relationship(
                source=source,
                target=target,
                type=Relationship.Type(annotation.relationship.type),
            ),
            extra={"uuid": annotation.uuid},
            feature_schema_id=annotation.schema_id,
        )

    @classmethod
    def from_common(
        cls,
        annotation: RelationshipAnnotation,
        data: Union[ImageData, TextData],
    ) -> "NDRelationship":
        relationship = annotation.value
        return cls(
            uuid=str(annotation._uuid),
            name=annotation.name,
            dataRow=DataRow(id=data.uid, global_key=data.global_key),
            relationship=_Relationship(
                source=str(relationship.source._uuid),
                target=str(relationship.target._uuid),
                type=relationship.type.value,
            ),
        )
