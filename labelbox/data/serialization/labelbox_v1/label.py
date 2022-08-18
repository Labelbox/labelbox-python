from labelbox.data.annotation_types.data.tiled_image import TiledImageData
from labelbox.utils import camel_case
from typing import List, Optional, Union, Dict, Any

from pydantic import BaseModel, Field

from ...annotation_types.annotation import (ClassificationAnnotation,
                                            ObjectAnnotation,
                                            VideoClassificationAnnotation,
                                            VideoObjectAnnotation)
from ...annotation_types.data import ImageData, TextData, VideoData
from ...annotation_types.label import Label
from .classification import LBV1Classifications
from .objects import LBV1Objects, LBV1TextEntity


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

    def to_common(
        self
    ) -> List[Union[VideoClassificationAnnotation, VideoObjectAnnotation]]:
        classifications = [
            VideoClassificationAnnotation(
                value=classification.to_common(),
                frame=self.frame_number,
                name=classification.title,
                feature_schema_id=classification.schema_id)
            for classification in self.classifications
        ]

        objects = [
            VideoObjectAnnotation(value=obj.to_common(),
                                  keyframe=obj.keyframe,
                                  classifications=[
                                      ClassificationAnnotation(
                                          value=cls.to_common(),
                                          feature_schema_id=cls.schema_id,
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
                                  feature_schema_id=obj.schema_id,
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
    data_row_media_attributes: Optional[Dict[str, Any]] = Field(
        {}, alias="Media Attributes")
    data_row_metadata: Optional[List[Dict[str, Any]]] = Field(
        [], alias="DataRow Metadata")

    created_by: Optional[str] = Extra('Created By')
    project_name: Optional[str] = Extra('Project Name')
    created_at: Optional[str] = Extra('Created At')
    updated_at: Optional[str] = Extra('Updated At')
    seconds_to_label: Optional[float] = Extra('Seconds to Label')
    agreement: Optional[float] = Extra('Agreement')
    benchmark_agreement: Optional[float] = Extra('Benchmark Agreement')
    benchmark_id: Optional[str] = Extra('Benchmark ID')
    dataset_name: Optional[str] = Extra('Dataset Name')
    reviews: Optional[List[Review]] = Extra('Reviews')
    label_url: Optional[str] = Extra('View Label')
    has_open_issues: Optional[float] = Extra('Has Open Issues')
    skipped: Optional[bool] = Extra('Skipped')
    media_type: Optional[str] = Extra('media_type')
    data_split: Optional[str] = Extra('Data Split')
    global_key: Optional[str] = Extra('Global Key')

    def to_common(self) -> Label:
        if isinstance(self.label, list):
            annotations = []
            for lbl in self.label:
                annotations.extend(lbl.to_common())
        else:
            annotations = self.label.to_common()

        return Label(data=self._data_row_to_common(),
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
                         data_row_media_attributes=label.data.media_attributes,
                         data_row_metadata=label.data.metadata,
                         **label.extra)

    def _data_row_to_common(
            self) -> Union[ImageData, TextData, VideoData, TiledImageData]:
        # Use data row information to construct the appropriate annotation type
        data_row_info = {
            'url' if self._is_url() else 'text': self.row_data,
            'external_id': self.external_id,
            'uid': self.data_row_id,
            'media_attributes': self.data_row_media_attributes,
            'metadata': self.data_row_metadata
        }

        self.media_type = self.media_type or self._infer_media_type()
        media_mapping = {
            'text': TextData,
            'image': ImageData,
            'video': VideoData
        }
        if self.media_type not in media_mapping:
            raise ValueError(
                f"Annotation types are only supported for {list(media_mapping)} media types."
                f" Found {self.media_type}.")
        return media_mapping[self.media_type](**data_row_info)

    def _infer_media_type(self) -> str:
        # Determines the data row type based on the label content
        if isinstance(self.label, list):
            return 'video'
        if self._has_text_annotations():
            return 'text'
        elif self._has_object_annotations():
            return 'image'
        else:
            if self._row_contains((".jpg", ".png", ".jpeg")) and self._is_url():
                return 'image'
            elif (self._row_contains((".txt", ".text", ".html")) and
                  self._is_url()) or not self._is_url():
                return 'text'
            else:
                #  This condition will occur when a data row url does not contain a file extension
                #  and the label does not contain object annotations that indicate the media type.
                #  As a temporary workaround you can explicitly set the media_type
                #  in each label json payload before converting.
                #  We will eventually provide the media type in the export.
                raise TypeError(
                    f"Can't infer data type from row data. row_data: {self.row_data[:200]}"
                )

    def _has_object_annotations(self) -> bool:
        return len(self.label.objects) > 0

    def _has_text_annotations(self) -> bool:
        return len([
            annotation for annotation in self.label.objects
            if isinstance(annotation, LBV1TextEntity)
        ]) > 0

    def _row_contains(self, substrs) -> bool:
        return any([substr in self.row_data for substr in substrs])

    def _is_url(self) -> bool:
        return self.row_data.startswith(
            ("http://", "https://", "gs://",
             "s3://")) or "tileLayerUrl" in self.row_data

    class Config:
        allow_population_by_field_name = True