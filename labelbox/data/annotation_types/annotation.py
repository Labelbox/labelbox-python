from typing import List, Optional, Union
from uuid import uuid4
from pydantic import BaseModel
from labelbox.data.annotation_types.reference import FeatureSchemaRef
from labelbox.schema.ontology import OntologyBuilder
from labelbox.data.annotation_types.classification.classification import Classification
from labelbox.data.annotation_types.data.video import VideoData
from labelbox.data.annotation_types.ner import TextEntity
from labelbox.data.annotation_types.geometry.geometry import Geometry
from labelbox.data.annotation_types.classification.classification import (
    Radio, CheckList, Text, Dropdown)


class Annotation(BaseModel):
    feature_id: Optional[
        str] = None  # Can be used to reference the feature in labelbox
    feature_schema_ref: FeatureSchemaRef  # This is not super meaningful to non-labelbox users. It is more the feature_type_id
    classifications: Optional[List[Union[Radio, CheckList, Text,
                                         Dropdown]]] = None
    value: Union[Classification, Geometry, TextEntity]

    def to_mal_ndjson(self, ontology: OntologyBuilder):
        if self.value is None:
            raise ValueError("")

        return {
            "uuid":
                str(uuid4()),
            'schemaId':
                self.schema_id,
            **self.value.to_mal_ndjson(), "classifications": [
                classification.to_mal_subclass_ndjson()
                for classification in self.classifications
            ]
        }


class Frames(BaseModel):
    start: int
    end: int


class VideoAnnotation(Annotation):
    data: VideoData
    frames: List[Frames] = []

    def to_mal_ndjson(self, ontology: OntologyBuilder):
        payload = super(VideoAnnotation, self).to_mal_ndjson(ontology)
        payload.update({
            'frames': [{
                "start": frame.start,
                "end": frame.end
            } for frame in self.frames]
        })
