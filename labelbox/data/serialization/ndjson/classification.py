from typing import Any, Dict, List, Union, Optional

from pydantic import BaseModel, Field, validator

from labelbox.utils import camel_case
from ...annotation_types.annotation import ClassificationAnnotation, VideoClassificationAnnotation
from ...annotation_types.classification.classification import ClassificationAnswer, Dropdown, Text, Checklist, Radio
from ...annotation_types.types import Cuid
from ...annotation_types.data import TextData, VideoData, ImageData
from .base import NDAnnotation


class NDFeature(BaseModel):
    schema_id: Cuid

    @validator('schema_id', pre=True, always=True)
    def validate_id(cls, v):
        if v is None:
            raise ValueError(
                "Schema ids are not set. Use `LabelGenerator.assign_schema_ids`, `LabelList.assign_schema_ids`, or `Label.assign_schema_ids`."
            )
        return v

    class Config:
        allow_population_by_field_name = True
        alias_generator = camel_case


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
    def from_common(cls, text: Text, schema_id: Cuid) -> "NDTextSubclass":
        return cls(answer=text.answer, schema_id=schema_id)


class NDChecklistSubclass(NDFeature):
    answer: List[NDFeature] = Field(..., alias='answers')

    def to_common(self) -> Checklist:
        return Checklist(answer=[
            ClassificationAnswer(schema_id=answer.schema_id)
            for answer in self.answer
        ])

    @classmethod
    def from_common(cls, checklist: Checklist,
                    schema_id: Cuid) -> "NDChecklistSubclass":
        return cls(answer=[
            NDFeature(schema_id=answer.schema_id) for answer in checklist.answer
        ],
                   schema_id=schema_id)

    def dict(self, *args, **kwargs):
        res = super().dict(*args, **kwargs)
        if 'answers' in res:
            res['answer'] = res.pop('answers')
        return res


class NDRadioSubclass(NDFeature):
    answer: NDFeature

    def to_common(self) -> Radio:
        return Radio(answer=ClassificationAnswer(
            schema_id=self.answer.schema_id))

    @classmethod
    def from_common(cls, radio: Radio, schema_id: Cuid) -> "NDRadioSubclass":
        return cls(answer=NDFeature(schema_id=radio.answer.schema_id),
                   schema_id=schema_id)


### ====== End of subclasses


class NDText(NDAnnotation, NDTextSubclass):

    @classmethod
    def from_common(cls, text: Text, schema_id: Cuid, extra: Dict[str, Any],
                    data: Union[TextData, ImageData]) -> "NDText":
        return cls(
            answer=text.answer,
            data_row={'id': data.uid},
            schema_id=schema_id,
            uuid=extra.get('uuid'),
        )


class NDChecklist(NDAnnotation, NDChecklistSubclass, VideoSupported):

    @classmethod
    def from_common(
            cls, checklist: Checklist, schema_id: Cuid, extra: Dict[str, Any],
            data: Union[VideoData, TextData, ImageData]) -> "NDChecklist":
        return cls(answer=[
            NDFeature(schema_id=answer.schema_id) for answer in checklist.answer
        ],
                   data_row={'id': data.uid},
                   schema_id=schema_id,
                   uuid=extra.get('uuid'),
                   frames=extra.get('frames'))


class NDRadio(NDAnnotation, NDRadioSubclass, VideoSupported):

    @classmethod
    def from_common(cls, radio: Radio, schema_id: Cuid, extra: Dict[str, Any],
                    data: Union[VideoData, TextData, ImageData]) -> "NDRadio":
        return cls(answer=NDFeature(schema_id=radio.answer.schema_id),
                   data_row={'id': data.uid},
                   schema_id=schema_id,
                   uuid=extra.get('uuid'),
                   frames=extra.get('frames'))


class NDSubclassification:

    @classmethod
    def from_common(
        cls, annotation: ClassificationAnnotation
    ) -> Union[NDTextSubclass, NDChecklistSubclass, NDRadioSubclass]:
        classify_obj = cls.lookup_subclassification(annotation)
        if classify_obj is None:
            raise TypeError(
                f"Unable to convert object to MAL format. `{type(annotation.value)}`"
            )
        return classify_obj.from_common(annotation.value, annotation.schema_id)

    @staticmethod
    def to_common(
            annotation: "NDClassificationType") -> ClassificationAnnotation:
        return ClassificationAnnotation(value=annotation.to_common(),
                                        schema_id=annotation.schema_id)

    @staticmethod
    def lookup_subclassification(
        annotation: ClassificationAnnotation
    ) -> Union[NDTextSubclass, NDChecklistSubclass, NDRadioSubclass]:
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
        annotation: "NDClassificationType"
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
        cls, annotation: Union[ClassificationAnnotation,
                               VideoClassificationAnnotation],
        data: Union[VideoData, TextData, ImageData]
    ) -> Union[NDTextSubclass, NDChecklistSubclass, NDRadioSubclass]:
        classify_obj = cls.lookup_classification(annotation)
        if classify_obj is None:
            raise TypeError(
                f"Unable to convert object to MAL format. `{type(annotation.value)}`"
            )
        return classify_obj.from_common(annotation.value, annotation.schema_id,
                                        annotation.extra, data)

    @staticmethod
    def lookup_classification(
        annotation: Union[ClassificationAnnotation,
                          VideoClassificationAnnotation]
    ) -> Union[NDText, NDChecklist, NDRadio]:
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
