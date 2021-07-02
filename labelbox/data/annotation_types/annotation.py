"""
Annotation objects

https://labelbox.quip.com/vaSkAOkR9bU3/Predictions-InputOutput-Format
Takes inspiration from label export formats
https://labelbox.com/docs/exporting-data/old-vs-new-exports

"""

from labelbox.data.annotation_types.classification.subclass import DropdownSubclass
from labelbox.schema.ontology import OntologyBuilder
from labelbox.data.annotation_types.classification.classification import Classification
from labelbox.data.annotation_types.data.video import VideoData
from labelbox.data.annotation_types.ner import TextEntity
from labelbox.data.annotation_types.geometry.geometry import Geometry
from labelbox.data.annotation_types import classification
from labelbox.data.annotation_types.data.text import TextData
import marshmallow_dataclass
from functools import cached_property
from typing import Any, Dict, Generator, List, NewType, Optional, Set, Union
from labelbox.data.annotation_types.data.raster import (
    RasterData,
)
from uuid import uuid4

from labelbox.data.annotation_types.classification.classification import (
    Radio,
    CheckList,
    Text,
    Dropdown
)
from labelbox.data.annotation_types.marshmallow import Uuid, default_none, required



@marshmallow_dataclass.dataclass
class Annotation:
    schema_id: str = default_none()
    name: str = default_none()
    classifications: Optional[
        List[Union[Radio, CheckList, Text, Dropdown]]
    ] = default_none()
    value: Union[Classification, Geometry, TextEntity]

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
    data: VideoData = default_none()
    frames: List[Frames]

    def to_mal_ndjson(self, ontology: OntologyBuilder):
        payload = super(VideoAnnotation, self).to_mal_ndjson(ontology)
        payload.update({
            'frames' : [{"start" : frame.start, "end" : frame.end} for frame in self.frames ]
        })
