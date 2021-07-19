from labelbox.data.annotation_types.classification.classification import CheckList, Dropdown, Radio, Text
from labelbox.data.annotation_types.ner import TextEntity
from labelbox.data.annotation_types.annotation import AnnotationType, ClassificationAnnotation, ObjectAnnotation, VideoAnnotationType, VideoClassificationAnnotation, VideoObjectAnnotation
from labelbox.data.annotation_types.data.video import VideoData
from labelbox.data.annotation_types.data.text import TextData
from labelbox.data.annotation_types.data.raster import RasterData
from labelbox.data.annotation_types.label import Label
from labelbox.data.annotation_types.geometry.line import Line
from labelbox.data.annotation_types.geometry.point import Point
from labelbox.data.annotation_types.geometry.polygon import Polygon
from labelbox.data.annotation_types.geometry.rectangle import Rectangle
from labelbox.data.annotation_types.geometry.mask import Mask
from labelbox.data.serialization.labelbox_v1.objects import LBV1Line, LBV1Mask, LBV1Objects, LBV1Point, LBV1Polygon, LBV1Rectangle, LBV1TextEntity
from labelbox.data.serialization.labelbox_v1.classifications import LBV1Classifications, LBV1Radio, LBV1Checklist, LBV1Text
from pydantic import BaseModel, Field
from typing import Callable, List, Union, Optional


class _LBV1Label(LBV1Classifications, LBV1Objects):
    def to_common(self):
        classifications = LBV1Classifications.to_common(self)
        objects = LBV1Objects.to_common(self)
        return [*objects, *classifications]

    @classmethod
    def from_common(cls, annotations: List[AnnotationType]) -> "_LBV1Label":
        objects = LBV1Objects.from_common([x for x in annotations if isinstance(x, ObjectAnnotation)])
        classifications = LBV1Classifications.from_common([x for x in annotations if isinstance(x, ClassificationAnnotation)])
        return cls(**objects.dict(), **classifications.dict())




class _LBV1LabelVideo(_LBV1Label):
    frame_number : int = Field(..., alias = 'frameNumber')

    def to_common(self):
        classifications = [
            VideoClassificationAnnotation(value=classification.to_common(),
                       # Labelbox doesn't support subclasses on image level classifications
                       # These are added to top level classifications
                       classifications=[],
                       #keyframe = classification.keyframe,
                       frame = self.frame_number,
                       display_name=classification.title)
            for classification in self.classifications
        ]

        objects = [
            VideoObjectAnnotation(
                value=obj.to_common(),
                keyframe = obj.keyframe,
                classifications=[
                           ClassificationAnnotation(value=cls.to_common(),
                                    schema_id = cls.schema_id,
                                    display_name=cls.title, extra = {'feature_id' : cls.feature_id, 'title' : cls.title, 'value' : cls.value})
                           for cls in obj.classifications
                       ],
                display_name=obj.title,
                frame = self.frame_number,
                alternative_name = obj.value,
                schema_id = obj.schema_id,
                extra = {
                    'instanceURI' : obj.instanceURI,
                    'color' : obj.color,
                    'feature_id' : obj.feature_id,
                }
                )
            for obj in self.objects
        ]
        return [*classifications, *objects]

    @classmethod
    def from_common(self, annotations: List[VideoAnnotationType]) -> "_LBV1LabelVideo":
        by_frames = {}
        for annotation in annotations:
            if annotation.frame in by_frames:
                by_frames[annotation.frame].append(annotation)
            else:
                by_frames[annotation.frame] = [annotation]

        result = []
        for frame in by_frames:
            converted = _LBV1Label.from_common(annotations=by_frames[frame])
            result.append(_LBV1LabelVideo(frame_number = frame, objects = converted.objects, classifications = converted.classifications))

        return result

    class Config:
        allow_population_by_field_name = True



class Review(BaseModel):
    score: int
    id: str
    created_at: str = Field(..., alias = "createdAt")
    created_by: str = Field(..., alias = "createdBy")
    label_id: str = Field(..., alias = "labelId")

# TODO: Rename this to LBV1Example and _LBV1Label to LBV1Label
class LBV1Label(BaseModel):
    label: Union[_LBV1Label, List[_LBV1LabelVideo]] = Field(..., alias='Label')
    data_row_id: str = Field(..., alias="DataRow ID")
    row_data: str = Field(..., alias="Labeled Data")
    external_id: Optional[str] = Field(None, alias="External ID")
    created_by: Optional[str] = Field(None, alias = 'Created By')

    id: Optional[str] = Field(None, alias = 'ID')
    project_name: Optional[str] = Field(None, alias = 'Project Name')
    created_at: Optional[str] = Field(None, alias = 'Created At')
    updated_at: Optional[str] = Field(None, alias = 'Updated At')
    seconds_to_label: Optional[float] = Field(None, alias = 'Seconds to Label')
    agreement: Optional[float] = Field(None, alias = 'Agreement')
    benchmark_agreement: Optional[float] = Field(None, alias = 'Benchmark Agreement')
    benchmark_id: Optional[float] = Field(None, alias = 'Benchmark ID')
    dataset_name: Optional[str] = Field(None, alias = 'Dataset Name')
    reviews: Optional[List[Review]] = Field(None, alias = 'Reviews')
    label_url: Optional[str] = Field(None, alias = 'View Label')
    has_open_issues: Optional[float] = Field(None, alias = 'Has Open Issues')
    skipped: Optional[bool] = Field(None, alias = 'Skipped')


    def construct_data_ref(self, is_video):
        # TODO: Let users specify the type ...
        keys = {'external_id': self.external_id, 'uid': self.data_row_id}

        if is_video:
            return VideoData(url = self.row_data, **keys)
        if any([x in self.row_data for x in (".jpg", ".png", ".jpeg")]) and self.row_data.startswith(("http://", "https://")):
            return RasterData(url=self.row_data, **keys)
        elif any([x in self.row_data for x in (".txt", ".text", ".html")]) and self.row_data.startswith(("http://", "https://")):
            return TextData(url=self.row_data, **keys)
        elif isinstance(self.row_data, str):
            return TextData(text=self.row_data, **keys)
        elif len([
                annotation for annotation in self.label.objects
                if isinstance(annotation, TextEntity)
        ]):
            return TextData(url=self.row_data, **keys)
        else:
            raise TypeError("Can't infer data type from row data.")

    def to_common(self, is_video = False) -> Label:
        if not is_video:
            annotations = self.label.to_common()
        else:
            annotations = []
            for lbl in self.label:
                annotations.extend(lbl.to_common())

        lbll= Label(data=self.construct_data_ref(is_video),
                     annotations=annotations,
                     extra = {
                         'Created By': self.created_by,
                         'Project Name' : self.project_name,
                         'ID'  :self.id,
                         'Created At' : self.created_at,
                         'Updated At' : self.updated_at,
                         'Seconds to Label' : self.seconds_to_label,
                         'Agreement': self.agreement,
                         'Benchmark Agreement': self.benchmark_agreement,
                         'Benchmark ID' : self.benchmark_id,
                         'Dataset Name' : self.dataset_name,
                         'Reviews' : [review.dict(by_alias = True) for review in self.reviews],
                         'View Label' : self.label_url,
                         'Has Open Issues' : self.has_open_issues,
                         'Skipped' : self.skipped
                    })
        return lbll

    @classmethod
    def from_common(cls, label: Label, signer: Callable):
        if isinstance(label.annotations[0], (VideoObjectAnnotation, VideoClassificationAnnotation)):
            label_ = _LBV1LabelVideo.from_common(label.annotations)
        else:
            label_ = _LBV1Label.from_common(label.annotations)

        return LBV1Label(label=label_,
                         data_row_id=label.data.uid,
                         row_data=label.data.create_url(signer),
                         external_id=label.data.external_id, **label.extra)

    class Config:
        allow_population_by_field_name = True
