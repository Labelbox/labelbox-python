from typing import Callable, List, Optional, Union

from pydantic import BaseModel, Field

from ...annotation_types.annotation import (
    AnnotationType, ClassificationAnnotation, ObjectAnnotation,
    VideoAnnotationType, VideoClassificationAnnotation, VideoObjectAnnotation)
from ...annotation_types.data import RasterData, TextData, VideoData
from ...annotation_types.label import Label
from ...annotation_types.ner import TextEntity
from .classification import LBV1Classifications
from .objects import LBV1Objects


class _LBV1Label(LBV1Classifications, LBV1Objects):

    def to_common(self):
        classifications = LBV1Classifications.to_common(self)
        objects = LBV1Objects.to_common(self)
        return [*objects, *classifications]

    @classmethod
    def from_common(cls, annotations: List[AnnotationType]) -> "_LBV1Label":

        objects = LBV1Objects.from_common(
            [x for x in annotations if isinstance(x, ObjectAnnotation)])
        classifications = LBV1Classifications.from_common(
            [x for x in annotations if isinstance(x, ClassificationAnnotation)])
        return cls(**objects.dict(), **classifications.dict())


class _LBV1LabelVideo(_LBV1Label):
    frame_number: int = Field(..., alias='frameNumber')

    def to_common(self):
        classifications = [
            VideoClassificationAnnotation(
                value=classification.to_common(),
                # Labelbox doesn't support subclasses on image level classifications
                # These are added to top level classifications
                classifications=[],
                frame=self.frame_number,
                name=classification.title)
            for classification in self.classifications
        ]

        objects = [
            VideoObjectAnnotation(
                value=obj.to_common(),
                keyframe=obj.keyframe,
                classifications=[
                    ClassificationAnnotation(
                        value=cls.to_common(),
                        schema_id=cls.schema_id,
                        name=cls.title,
                        extra={
                            'feature_id': cls.feature_id,
                            'title': cls.title,
                            'value': cls.value,
                            #'keyframe': getattr(cls, 'keyframe', None)
                        }) for cls in obj.classifications
                ],
                name=obj.title,
                frame=self.frame_number,
                alternative_name=obj.value,
                schema_id=obj.schema_id,
                extra={
                    'value': obj.value,
                    'instanceURI': obj.instanceURI,
                    'color': obj.color,
                    'feature_id': obj.feature_id,
                }) for obj in self.objects
        ]
        return [*classifications, *objects]

    @classmethod
    def from_common(
            cls, annotations: List[VideoAnnotationType]) -> "_LBV1LabelVideo":
        by_frames = {}
        for annotation in annotations:
            if annotation.frame in by_frames:
                by_frames[annotation.frame].append(annotation)
            else:
                by_frames[annotation.frame] = [annotation]

        result = []
        for frame in by_frames:
            converted = _LBV1Label.from_common(annotations=by_frames[frame])
            result.append(
                _LBV1LabelVideo(frame_number=frame,
                                objects=converted.objects,
                                classifications=converted.classifications))

        return result

    class Config:
        allow_population_by_field_name = True


class Review(BaseModel):
    score: int
    id: str
    created_at: str = Field(..., alias="createdAt")
    created_by: str = Field(..., alias="createdBy")
    label_id: str = Field(..., alias="labelId")


class LBV1Label(BaseModel):
    label: Union[_LBV1Label, List[_LBV1LabelVideo]] = Field(..., alias='Label')
    data_row_id: str = Field(..., alias="DataRow ID")
    row_data: str = Field(..., alias="Labeled Data")
    external_id: Optional[str] = Field(None, alias="External ID")

    created_by: Optional[str] = Field(None,
                                      alias='Created By',
                                      extra_field=True)
    project_name: Optional[str] = Field(None,
                                        alias='Project Name',
                                        extra_field=True)
    id: Optional[str] = Field(None, alias='ID', extra_field=True)
    created_at: Optional[str] = Field(None,
                                      alias='Created At',
                                      extra_field=True)
    updated_at: Optional[str] = Field(None,
                                      alias='Updated At',
                                      extra_field=True)
    seconds_to_label: Optional[float] = Field(None,
                                              alias='Seconds to Label',
                                              extra_field=True)
    agreement: Optional[float] = Field(None,
                                       alias='Agreement',
                                       extra_field=True)
    benchmark_agreement: Optional[float] = Field(None,
                                                 alias='Benchmark Agreement',
                                                 extra_field=True)
    benchmark_id: Optional[float] = Field(None,
                                          alias='Benchmark ID',
                                          extra_field=True)
    dataset_name: Optional[str] = Field(None,
                                        alias='Dataset Name',
                                        extra_field=True)
    reviews: Optional[List[Review]] = Field(None,
                                            alias='Reviews',
                                            extra_field=True)
    label_url: Optional[str] = Field(None, alias='View Label', extra_field=True)
    has_open_issues: Optional[float] = Field(None,
                                             alias='Has Open Issues',
                                             extra_field=True)
    skipped: Optional[bool] = Field(None, alias='Skipped', extra_field=True)

    def to_common(self) -> Label:
        if isinstance(self.label, list):
            annotations = []
            for lbl in self.label:
                annotations.extend(lbl.to_common())
            data = VideoData(url=self.row_data,
                             external_id=self.external_id,
                             uid=self.data_row_id)
        else:
            annotations = self.label.to_common()
            data = self._infer_media_type()

        return Label(data=data,
                     annotations=annotations,
                     extra={
                         field.alias: getattr(self, field_name)
                         for field_name, field in self.__fields__.items()
                         if field.field_info.extra.get('extra_field')
                     })

    @classmethod
    def from_common(cls, label: Label, signer: Callable[[bytes], str]):
        if isinstance(label.annotations[0],
                      (VideoObjectAnnotation, VideoClassificationAnnotation)):
            label_ = _LBV1LabelVideo.from_common(label.annotations)
        else:
            label_ = _LBV1Label.from_common(label.annotations)

        return LBV1Label(label=label_,
                         data_row_id=label.data.uid,
                         row_data=label.data.create_url(signer),
                         external_id=label.data.external_id,
                         **label.extra)

    def _infer_media_type(self):
        keys = {'external_id': self.external_id, 'uid': self.data_row_id}
        if any([x in self.row_data for x in (".jpg", ".png", ".jpeg")
               ]) and self.row_data.startswith(("http://", "https://")):
            return RasterData(url=self.row_data, **keys)
        elif any([x in self.row_data for x in (".txt", ".text", ".html")
                 ]) and self.row_data.startswith(("http://", "https://")):
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

    class Config:
        allow_population_by_field_name = True
