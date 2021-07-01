"""
Annotation objects

https://labelbox.quip.com/vaSkAOkR9bU3/Predictions-InputOutput-Format
Takes inspiration from label export formats
https://labelbox.com/docs/exporting-data/old-vs-new-exports

"""

from labelbox.data.annotation_types.ner import NER
from labelbox.data.annotation_types.geometry.geometry import Geometry
from labelbox.data.annotation_types import classification
from labelbox.data.annotation_types.data.text import TextData
import marshmallow_dataclass
from functools import cached_property
from typing import Any, Dict, Generator, List, NewType, Optional, Set, Union
from labelbox.data.annotation_types.data.raster import (
    RasterData,
)

from labelbox.data.annotation_types.subclass import (
    CheckListSubclass,
    RadioSubclass,
    TextSubclass,
)
import marshmallow
from io import BytesIO
import numpy as np
import requests
from labelbox.data.annotation_types.marshmallow import Uuid, default_none, required


@marshmallow_dataclass.dataclass
class Annotation:
    uuid: Uuid = required()  # TODO: automatically generate uuids
    data: Union[RasterData, TextData] = default_none()
    schema_id: str = default_none()
    name: str = default_none()
    classifications: Optional[
        List[Union[RadioSubclass, CheckListSubclass, TextSubclass, DropdownSubclass]]
    ] = default_none()
    value: Union[classification, Geometry, TextEntity]


@marshmallow_dataclass.dataclass
class Frames:
    start: int
    end: int

@marshmallow_dataclass.dataclass
class VideoAnnotation(Annotation):
    data: VideoData = default_none()
    frames: List[Frames]
