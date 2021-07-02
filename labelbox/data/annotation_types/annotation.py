from typing import List, Optional, Union
from uuid import uuid4
import marshmallow_dataclass

from labelbox.data.annotation_types.marshmallow import default_none, required
from labelbox.data.annotation_types.reference import FeatureSchemaRef
from labelbox.schema.ontology import OntologyBuilder
from labelbox.data.annotation_types.classification.classification import Classification
from labelbox.data.annotation_types.data.video import VideoData
from labelbox.data.annotation_types.ner import TextEntity
from labelbox.data.annotation_types.geometry.geometry import Geometry
from labelbox.data.annotation_types.classification.classification import (
    Radio,
    CheckList,
    Text,
    Dropdown
)

@marshmallow_dataclass.dataclass
class Annotation():
    feature_id: Optional[str] = default_none() # Can be used to reference the feature in labelbox
    feature_schema_ref: FeatureSchemaRef = required() # This is not super meaningful to non-labelbox users. It is more the feature_type_id
    classifications: Optional[
        List[Union[Radio, CheckList, Text, Dropdown]]
    ] = default_none()
    value: Union[Classification, Geometry, TextEntity] = required()

    def to_mal_ndjson(self, ontology: OntologyBuilder):
        if self.value is None:
            raise ValueError("")

        return {
            "uuid" : str(uuid4()),
            'schemaId' : self.schema_id,
            ** self.value.to_mal_ndjson(),
            "classifications" : [classification.to_mal_subclass_ndjson() for classification in self.classifications]
        }

@marshmallow_dataclass.dataclass
class Frames:
    start: int
    end: int

@marshmallow_dataclass.dataclass
class VideoAnnotation(Annotation):
    data: VideoData = required()
    frames: List[Frames] = []

    def to_mal_ndjson(self, ontology: OntologyBuilder):
        payload = super(VideoAnnotation, self).to_mal_ndjson(ontology)
        payload.update({
            'frames' : [{"start" : frame.start, "end" : frame.end} for frame in self.frames ]
        })
