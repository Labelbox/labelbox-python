from labelbox.data.annotation_types.classification.classification import CheckList, Dropdown, Radio, Text
from labelbox.data.annotation_types.ner import TextEntity
from labelbox.data.annotation_types.annotation import Annotation
from labelbox.data.annotation_types import classification
from labelbox.data.annotation_types.data.video import VideoData
from labelbox.data.annotation_types.data.text import TextData
from labelbox.data.annotation_types.data.raster import RasterData
from labelbox.data.annotation_types.label import Label
from labelbox.data.annotation_types.geometry.line import Line
from labelbox.data.annotation_types.geometry.point import Point
from labelbox.data.annotation_types.geometry.polygon import Polygon
from labelbox.data.annotation_types.geometry.rectangle import Rectangle
from labelbox.data.annotation_types.geometry.mask import Mask
from labelbox.data.serialization.labelbox_v1.objects import LBV1Line, LBV1Mask, LBV1Object, LBV1Point, LBV1Polygon, LBV1Rectangle
from labelbox.data.serialization.labelbox_v1.classifications import LBV1Radio, LBV1Checklist, LBV1Text
from pydantic import BaseModel, Field
from typing import Callable, List, Union


# TODO: Use the meta field on the interface objects to support maintaing info
# Even if it doesn't have a place or really matter...

class _LBV1Label(BaseModel):
    objects: List[LBV1Object]
    classifications: List[Union[LBV1Radio, LBV1Checklist, LBV1Text]] = []

    def to_common(self):
        classifications = [
            classification.to_common()
            for classification in self.classifications
        ]
        objects = [obj.to_common() for obj in self.objects]
        return [*classifications, *objects]

    def lookup_object(self, annotation: Annotation):
        return {
                Line : LBV1Line,
                Point: LBV1Point,
                Polygon: LBV1Polygon,
                Rectangle: LBV1Rectangle,
                Mask: LBV1Mask
            }.get(type(annotation.value))

    def lookup_classification(self, annotation: Annotation):
        return {
                Text: LBV1Text,
                Dropdown: LBV1Checklist,
                CheckList: LBV1Checklist,
                Radio: LBV1Radio,
            }.get(type(annotation.value))


    def from_common(self, annotations: List[Annotation]):
        objects = []
        classifications = []
        for annotation in annotations:
            obj = self.lookup_object(annotation)
            classification = self.lookup_classification(annotation)
            if obj is not None:
                raise TypeError(f"Unexpected type {type(annotation.value)}")
            elif classification is not None:
                return objects.append(obj.from_common(annotation.value, annotation.classifications))







class LBV1Label(BaseModel):
    label: _LBV1Label = Field(..., alias='Label')
    data_row_id: str = Field(..., alias="DataRow ID")
    row_data: str = Field(..., alias="Labeled Data")
    external_id: str = Field(..., alias="External ID")

    def construct_data_ref(self):
        # TODO: I think we can tell if this is a video or not just based on the export format ...

        keys = {'external_id': self.external_id, 'uid': self.data_row_id}
        if self.row_data.endswith((".jpg", ".png", ".jpeg")):
            return RasterData(url=self.row_data, **keys)
        elif self.row_data.endswith((".txt", ".text")):
            return TextData(url=self.row_data, **keys)
        elif isinstance(self.row_data, str):
            return TextData(text=self.row_data)
        elif len([
                annotation for annotation in self.label.objects
                if isinstance(annotation, TextEntity)
        ]):
            return TextData(url=self.row_data)
        else:
            raise TypeError("Can't infer data type from row data.")

    def to_common(self) -> Label:
        return Label(data=self.construct_data_ref(),
                     annotations=self.label.to_common())

    @classmethod
    def from_common(cls, label: Label, signer: Callable):
        return LBV1Label(label=_LBV1Label.from_annotations(label.annotations),
                         data_row_id=label.data.uid,
                         row_data=label.data.create_url(signer),
1
                         external_id=label.data.external_id)
