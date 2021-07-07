from typing import List, Optional, Union
from uuid import uuid4
from pydantic import BaseModel

from labelbox.schema.ontology import OntologyBuilder
from labelbox.data.annotation_types.reference import FeatureSchemaRef
from labelbox.data.annotation_types.classification.classification import Classification, Subclass
from labelbox.data.annotation_types.ner import TextEntity
from labelbox.data.annotation_types.geometry.geometry import Geometry

class Annotation(FeatureSchemaRef):
    feature_id: Optional[
        str] = None  # Can be used to reference the feature in labelbox
    classifications: List[Subclass] = []
    value: Union[Classification, Geometry, TextEntity]


class Frames(BaseModel):
    start: int
    end: int


class VideoAnnotation(Annotation):
    frames: List[Frames] = []


