from typing import List, Union, Optional

from pydantic import BaseModel, validator, Field

from ...annotation_types.annotation import AnnotationType, ClassificationAnnotation, VideoClassificationAnnotation
from ...annotation_types.classification.classification import ClassificationAnswer, Dropdown, Text, Checklist, Radio
from .base import NDAnnotation


class NDFeature(BaseModel):
    schema_id: str = Field(..., alias='schemaId')

    @validator('schema_id', pre=True, always=True)
    def validate_id(cls, v):
        if v is None:
            raise ValueError(
                "Schema ids are not set. Use `LabelGenerator.assign_schema_ids`, `LabelCollection.assign_schema_ids`, or `Label.assign_schema_ids`."
            )
        return v

    class Config:
        allow_population_by_field_name = True


class FrameLocation(BaseModel):
    end: int
    start: int


class VideoSupported(BaseModel):
    #Note that frames are only allowed as top level inferences for video
    frames: Optional[List[FrameLocation]] = None

    def dict(self, *args, **kwargs):
        res = super().dict(*args, **kwargs)
        # This means these are no video frames ..
        if self.frames is None:
            res.pop('frames')
        return res


class NDTextSubclass(NDFeature):
    answer: str

    def to_common(self) -> Text:
        return Text(answer=self.answer)

    @classmethod
    def from_common(cls, annotation) -> "NDTextSubclass":
        return cls(answer=annotation.value.answer,
                   schema_id=annotation.schema_id)


class NDChecklistSubclass(NDFeature):
    answer: List[NDFeature]

    def to_common(self) -> Checklist:
        return Checklist(answer=[
            ClassificationAnswer(schema_id=answer.schema_id)
            for answer in self.answer
        ])

    @classmethod
    def from_common(cls, annotation) -> "NDChecklistSubclass":
        return cls(answer=[
            NDFeature(schema_id=answer.schema_id)
            for answer in annotation.value.answer
        ],
                   schema_id=annotation.schema_id)


class NDRadioSubclass(NDFeature):
    answer: NDFeature

    def to_common(self) -> Radio:
        return Radio(answer=ClassificationAnswer(
            schema_id=self.answer.schema_id))

    @classmethod
    def from_common(cls, annotation) -> "NDRadioSubclass":
        return cls(
            answer=NDFeature(schema_id=annotation.value.answer.schema_id),
            schema_id=annotation.schema_id)


### ====== End of subclasses


class NDText(NDAnnotation, NDTextSubclass):

    @classmethod
    def from_common(cls, annotation, data) -> "NDText":
        return cls(
            answer=annotation.value.answer,
            dataRow={'id': data.uid},
            schema_id=annotation.schema_id,
            uuid=annotation.extra.get('uuid'),
        )


class NDChecklist(NDAnnotation, NDChecklistSubclass, VideoSupported):

    @classmethod
    def from_common(cls, annotation, data) -> "NDChecklist":
        return cls(answer=[
            NDFeature(schema_id=answer.schema_id)
            for answer in annotation.value.answer
        ],
                   dataRow={'id': data.uid},
                   schema_id=annotation.schema_id,
                   uuid=annotation.extra.get('uuid'),
                   frames=annotation.extra.get('frames'))


class NDRadio(NDAnnotation, NDRadioSubclass, VideoSupported):

    @classmethod
    def from_common(cls, annotation, data) -> "NDRadio":
        return cls(
            answer=NDFeature(schema_id=annotation.value.answer.schema_id),
            dataRow={'id': data.uid},
            schema_id=annotation.schema_id,
            uuid=annotation.extra.get('uuid'),
            frames=annotation.extra.get('frames'))


class NDSubclassification:
    # TODO: Create a type for these unions
    @classmethod
    def from_common(
        cls, annotation: AnnotationType
    ) -> Union[NDTextSubclass, NDChecklistSubclass, NDRadioSubclass]:
        classify_obj = cls.lookup_subclassification(annotation)
        if classify_obj is None:
            raise TypeError(
                f"Unable to convert object to MAL format. `{type(annotation.value)}`"
            )
        return classify_obj.from_common(annotation)

    @staticmethod
    def to_common(annotation: AnnotationType) -> ClassificationAnnotation:
        return ClassificationAnnotation(value=annotation.to_common(),
                                        schema_id=annotation.schema_id)

    @staticmethod
    def lookup_subclassification(annotation: AnnotationType):
        if isinstance(annotation, Dropdown):
            raise TypeError("Dropdowns are not supported for MAL")
        return {
            Text: NDTextSubclass,
            Checklist: NDChecklistSubclass,
            Radio: NDRadioSubclass,
        }.get(type(annotation.value))


class NDClassification:

    @staticmethod
    def to_common(
        annotation: AnnotationType
    ) -> Union[ClassificationAnnotation, VideoClassificationAnnotation]:
        common = ClassificationAnnotation(value=annotation.to_common(),
                                          schema_id=annotation.schema_id,
                                          extra={'uuid': annotation.uuid})
        if getattr(annotation, 'frames', None) is None:
            return [common]
        results = []
        for frame in annotation.frames:
            for idx in range(frame.start, frame.end + 1, 1):
                results.append(
                    VideoClassificationAnnotation(frame=idx, **common.dict()))
        return results

    @classmethod
    def from_common(
            cls, annotation: AnnotationType, data
    ) -> Union[NDTextSubclass, NDChecklistSubclass, NDRadioSubclass]:
        classify_obj = cls.lookup_classification(annotation)
        if classify_obj is None:
            raise TypeError(
                f"Unable to convert object to MAL format. `{type(annotation.value)}`"
            )
        if len(annotation.classifications):
            raise ValueError(
                "Nested classifications not supported by this format")
        return classify_obj.from_common(annotation, data)

    @staticmethod
    def lookup_classification(annotation: AnnotationType):
        if isinstance(annotation, Dropdown):
            raise TypeError("Dropdowns are not supported for MAL")
        return {
            Text: NDText,
            Checklist: NDChecklist,
            Radio: NDRadio,
            Dropdown: NDChecklist,
        }.get(type(annotation.value))


NDSubclassificationType = Union[NDRadioSubclass, NDChecklistSubclass,
                                NDTextSubclass]
NDClassificationType = Union[NDRadio, NDChecklist, NDText]
