from typing import Union, List

from labelbox.schema.ontology import OntologyBuilder
from labelbox.data.annotation_types.annotation import Annotation
from labelbox.data.annotation_types.data.raster import RasterData
from labelbox.data.annotation_types.data.text import TextData
from labelbox.data.annotation_types.data.video import VideoData
from labelbox.data.annotation_types.metrics import Metric
from pydantic import BaseModel


class Label(BaseModel):
    # TODO: This sounds too much like the other label we need to rename this...
    data: Union[RasterData, TextData, VideoData]
    annotations: List[Union[Annotation, Metric]] = []
