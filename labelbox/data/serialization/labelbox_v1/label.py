from labelbox.utils import camel_case
from typing import List, Optional, Union

from pydantic import BaseModel, Field

from ...annotation_types.annotation import (ClassificationAnnotation,
                                            ObjectAnnotation,
                                            VideoClassificationAnnotation,
                                            VideoObjectAnnotation)
from ...annotation_types.data import RasterData, TextData, VideoData
from ...annotation_types.label import Label
from ...annotation_types.ner import TextEntity
from .classification import LBV1Classifications
from .objects import LBV1Objects


class LBV1LabelAnnotations(LBV1Classifications, LBV1Objects):

    def to_common(
            self) -> List[Union[ObjectAnnotation, ClassificationAnnotation]]:
        classifications = LBV1Classifications.to_common(self)
        objects = LBV1Objects.to_common(self)
        return [*objects, *classifications]

    @classmethod
    def from_common(
        cls, annotations: List[Union[ClassificationAnnotation,
                                     ObjectAnnotation]]
    ) -> "LBV1LabelAnnotations":

        objects = LBV1Objects.from_common(
            [x for x in annotations if isinstance(x, ObjectAnnotation)])
        classifications = LBV1Classifications.from_common(
            [x for x in annotations if isinstance(x, ClassificationAnnotation)])
        return cls(**objects.dict(), **classifications.dict())


class LBV1LabelAnnotationsVideo(LBV1LabelAnnotations):
    frame_number: int = Field(..., alias='frameNumber')

    def to_common(self):
        classifications = [
            VideoClassificationAnnotation(value=classification.to_common(),
                                          frame=self.frame_number,
                                          name=classification.title,
                                          schema_id=classification.schema_id)
            for classification in self.classifications
        ]

        objects = [
            VideoObjectAnnotation(value=obj.to_common(),
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
        cls, annotations: List[Union[VideoObjectAnnotation,
                                     VideoClassificationAnnotation]]
    ) -> "LBV1LabelAnnotationsVideo":
        by_frames = {}
        for annotation in annotations:
            if annotation.frame in by_frames:
                by_frames[annotation.frame].append(annotation)
            else:
                by_frames[annotation.frame] = [annotation]

        result = []
        for frame in by_frames:
            converted = LBV1LabelAnnotations.from_common(
                annotations=by_frames[frame])
            result.append(
                LBV1LabelAnnotationsVideo(
                    frame_number=frame,
                    objects=converted.objects,
                    classifications=converted.classifications))

        return result

    class Config:
        allow_population_by_field_name = True


class Review(BaseModel):
    score: int
    id: str
    created_at: str
    created_by: str
    label_id: str

    class Config:
        alias_generator = camel_case


Extra = lambda name: Field(None, alias=name, extra_field=True)


class LBV1Label(BaseModel):
    label: Union[LBV1LabelAnnotations,
                 List[LBV1LabelAnnotationsVideo]] = Field(..., alias='Label')
    data_row_id: str = Field(..., alias="DataRow ID")
    row_data: str = Field(None, alias="Labeled Data")
    id: Optional[str] = Field(None, alias='ID')
    external_id: Optional[str] = Field(None, alias="External ID")

    created_by: Optional[str] = Extra('Created By')
    project_name: Optional[str] = Extra('Project Name')
    created_at: Optional[str] = Extra('Created At')
    updated_at: Optional[str] = Extra('Updated At')
    seconds_to_label: Optional[float] = Extra('Seconds to Label')
    agreement: Optional[float] = Extra('Agreement')
    benchmark_agreement: Optional[float] = Extra('Benchmark Agreement')
    benchmark_id: Optional[float] = Extra('Benchmark ID')
    dataset_name: Optional[str] = Extra('Dataset Name')
    reviews: Optional[List[Review]] = Extra('Reviews')
    label_url: Optional[str] = Extra('View Label')
    has_open_issues: Optional[float] = Extra('Has Open Issues')
    skipped: Optional[bool] = Extra('Skipped')

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
                     uid=self.id,
                     annotations=annotations,
                     extra={
                         field.alias: getattr(self, field_name)
                         for field_name, field in self.__fields__.items()
                         if field.field_info.extra.get('extra_field')
                     })

    @classmethod
    def from_common(cls, label: Label):
        if isinstance(label.annotations[0],
                      (VideoObjectAnnotation, VideoClassificationAnnotation)):
            label_ = LBV1LabelAnnotationsVideo.from_common(label.annotations)
        else:
            label_ = LBV1LabelAnnotations.from_common(label.annotations)

        return LBV1Label(label=label_,
                         id=label.uid,
                         data_row_id=label.data.uid,
                         row_data=label.data.url,
                         external_id=label.data.external_id,
                         **label.extra)

    def _infer_media_type(self):
        # Video annotations are formatted differently from text and images
        # So we only need to differentiate those two
        data_row_info = {
            'external_id': self.external_id,
            'uid': self.data_row_id
        }

        if self._has_text_annotations():
            # If it has text annotations then it must be text
            if self._is_url():
                return TextData(url=self.row_data, **data_row_info)
            else:
                return TextData(text=self.row_data, **data_row_info)
        elif self._has_object_annotations():
            # If it has object annotations and none are text annotations then it must be an image
            if self._is_url():
                return RasterData(url=self.row_data, **data_row_info)
            else:
                return RasterData(text=self.row_data, **data_row_info)
        else:
            # no annotations to infer data type from.
            # Use information from the row_data format if possible.
            if self._row_contains((".jpg", ".png", ".jpeg")) and self._is_url():
                return RasterData(url=self.row_data, **data_row_info)
            elif self._row_contains(
                (".txt", ".text", ".html")) and self._is_url():
                return TextData(url=self.row_data, **data_row_info)
            elif not self._is_url():
                return TextData(text=self.row_data, **data_row_info)
            else:
                # This is going to be urls that do not contain any file extensions
                # This will only occur on skipped images.
                # To use this converter on data with this url format
                #   filter out empty examples from the payload before deserializing.
                raise TypeError(
                    "Can't infer data type from row data. Remove empty examples before trying again. "
                    f"row_data: {self.row_data[:200]}")

    def _has_object_annotations(self):
        return len(self.label.objects) > 0

    def _has_text_annotations(self):
        return len([
            annotation for annotation in self.label.objects
            if isinstance(annotation, TextEntity)
        ]) > 0

    def _row_contains(self, substrs):
        return any([substr in self.row_data for substr in substrs])

    def _is_url(self):
        return self.row_data.startswith(("http://", "https://"))

    class Config:
        allow_population_by_field_name = True
