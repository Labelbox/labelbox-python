from typing import Optional
from pydantic import BaseModel
from .base import NDAnnotation, DataRow
from ...annotation_types.data import GenericDataRowData
from ...annotation_types.relationship import RelationshipAnnotation
from ...annotation_types.relationship import Relationship
from .objects import NDObjectType
from .base import DataRow

SUPPORTED_ANNOTATIONS = NDObjectType


class _Relationship(BaseModel):
    source: Optional[str] = None
    target: str
    type: str
    readonly: Optional[bool] = None
    sourceOntologyName: Optional[str] = None


class NDRelationship(NDAnnotation):
    relationship: _Relationship

    @staticmethod
    def to_common(
        annotation: "NDRelationship",
        source: SUPPORTED_ANNOTATIONS,
        target: SUPPORTED_ANNOTATIONS,
        source_ontology_name: Optional[str] = None,
    ) -> RelationshipAnnotation:
        return RelationshipAnnotation(
            name=annotation.name,
            value=Relationship(
                source=source,
                source_ontology_name=source_ontology_name,
                target=target,
                type=Relationship.Type(annotation.relationship.type),
                readonly=annotation.relationship.readonly,
            ),
            extra={"uuid": annotation.uuid},
            feature_schema_id=annotation.schema_id,
        )

    @classmethod
    def from_common(
        cls,
        annotation: RelationshipAnnotation,
        data: GenericDataRowData,
    ) -> "NDRelationship":
        relationship = annotation.value
        return cls(
            uuid=str(annotation._uuid),
            name=annotation.name,
            dataRow=DataRow(id=data.uid, global_key=data.global_key),
            relationship=_Relationship(
                source=str(relationship.source._uuid)
                if relationship.source
                else None,
                target=str(relationship.target._uuid),
                sourceOntologyName=relationship.source_ontology_name,
                type=relationship.type.value,
                readonly=relationship.readonly,
            ),
        )
