from typing import Any, Dict, List, Union, Optional

from labelbox.data.annotation_types import ImageData, TextData, VideoData
from labelbox.data.mixins import (
    ConfidenceMixin,
    CustomMetric,
    CustomMetricsMixin,
)
from labelbox.data.serialization.ndjson.base import DataRow, NDAnnotation

from ....annotated_types import Cuid

from ...annotation_types.annotation import ClassificationAnnotation
from ...annotation_types.video import VideoClassificationAnnotation
from ...annotation_types.llm_prompt_response.prompt import (
    PromptClassificationAnnotation,
    PromptText,
)
from ...annotation_types.classification.classification import (
    ClassificationAnswer,
    Text,
    Checklist,
    Radio,
)
from pydantic import (
    model_validator,
    Field,
    BaseModel,
    ConfigDict,
    model_serializer,
)
from pydantic.alias_generators import to_camel
from .base import _SubclassRegistryBase


class NDAnswer(ConfidenceMixin, CustomMetricsMixin):
    name: Optional[str] = None
    schema_id: Optional[Cuid] = None
    classifications: Optional[List["NDSubclassificationType"]] = None
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    @model_validator(mode="after")
    def must_set_one(self):
        if (not hasattr(self, "schema_id") or self.schema_id is None) and (
            not hasattr(self, "name") or self.name is None
        ):
            raise ValueError("Schema id or name are not set. Set either one.")
        return self

    @model_serializer(mode="wrap")
    def serialize_model(self, handler):
        res = handler(self)
        if "name" in res and res["name"] is None:
            res.pop("name")
        if "schemaId" in res and res["schemaId"] is None:
            res.pop("schemaId")
        if self.classifications:
            res["classifications"] = [
                c.model_dump(exclude_none=True) for c in self.classifications
            ]
        return res


class FrameLocation(BaseModel):
    end: int
    start: int


class VideoSupported(BaseModel):
    # Note that frames are only allowed as top level inferences for video
    frames: Optional[List[FrameLocation]] = None

    @model_serializer(mode="wrap")
    def serialize_model(self, handler):
        res = handler(self)
        # This means these are no video frames ..
        if self.frames is None:
            res.pop("frames")
        return res


class NDTextSubclass(NDAnswer):
    answer: str

    def to_common(self) -> Text:
        return Text(
            answer=self.answer,
            confidence=self.confidence,
            custom_metrics=self.custom_metrics,
        )

    @classmethod
    def from_common(
        cls, text: Text, name: str, feature_schema_id: Cuid
    ) -> "NDTextSubclass":
        return cls(
            answer=text.answer,
            name=name,
            schema_id=feature_schema_id,
            confidence=text.confidence,
            custom_metrics=text.custom_metrics,
        )


class NDChecklistSubclass(NDAnswer):
    answer: List[NDAnswer] = Field(..., validation_alias="answers")

    def to_common(self) -> Checklist:
        return Checklist(
            answer=[
                ClassificationAnswer(
                    name=answer.name,
                    feature_schema_id=answer.schema_id,
                    confidence=answer.confidence,
                    classifications=[
                        NDSubclassification.to_common(annot)
                        for annot in answer.classifications
                    ]
                    if answer.classifications
                    else None,
                    custom_metrics=answer.custom_metrics,
                )
                for answer in self.answer
            ]
        )

    @classmethod
    def from_common(
        cls, checklist: Checklist, name: str, feature_schema_id: Cuid
    ) -> "NDChecklistSubclass":
        return cls(
            answer=[
                NDAnswer(
                    name=answer.name,
                    schema_id=answer.feature_schema_id,
                    confidence=answer.confidence,
                    classifications=[
                        NDSubclassification.from_common(annot)
                        for annot in answer.classifications
                    ]
                    if answer.classifications
                    else None,
                    custom_metrics=answer.custom_metrics,
                )
                for answer in checklist.answer
            ],
            name=name,
            schema_id=feature_schema_id,
        )

    @model_serializer(mode="wrap")
    def serialize_model(self, handler):
        res = handler(self)
        if "answers" in res:
            res["answer"] = res["answers"]
            del res["answers"]
        return res


class NDRadioSubclass(NDAnswer):
    answer: NDAnswer

    def to_common(self) -> Radio:
        return Radio(
            answer=ClassificationAnswer(
                name=self.answer.name,
                feature_schema_id=self.answer.schema_id,
                confidence=self.answer.confidence,
                classifications=[
                    NDSubclassification.to_common(annot)
                    for annot in self.answer.classifications
                ]
                if self.answer.classifications
                else None,
                custom_metrics=self.answer.custom_metrics,
            )
        )

    @classmethod
    def from_common(
        cls, radio: Radio, name: str, feature_schema_id: Cuid
    ) -> "NDRadioSubclass":
        return cls(
            answer=NDAnswer(
                name=radio.answer.name,
                schema_id=radio.answer.feature_schema_id,
                confidence=radio.answer.confidence,
                classifications=[
                    NDSubclassification.from_common(annot)
                    for annot in radio.answer.classifications
                ]
                if radio.answer.classifications
                else None,
                custom_metrics=radio.answer.custom_metrics,
            ),
            name=name,
            schema_id=feature_schema_id,
        )


class NDPromptTextSubclass(NDAnswer):
    answer: str

    def to_common(self) -> PromptText:
        return PromptText(
            answer=self.answer,
            confidence=self.confidence,
            custom_metrics=self.custom_metrics,
        )

    @classmethod
    def from_common(
        cls, prompt_text: PromptText, name: str, feature_schema_id: Cuid
    ) -> "NDPromptTextSubclass":
        return cls(
            answer=prompt_text.answer,
            name=name,
            schema_id=feature_schema_id,
            confidence=prompt_text.confidence,
            custom_metrics=prompt_text.custom_metrics,
        )


# ====== End of subclasses


class NDText(NDAnnotation, NDTextSubclass, _SubclassRegistryBase):
    @classmethod
    def from_common(
        cls,
        uuid: str,
        text: Text,
        name: str,
        feature_schema_id: Cuid,
        extra: Dict[str, Any],
        data: Union[TextData, ImageData],
        message_id: str,
        confidence: Optional[float] = None,
    ) -> "NDText":
        return cls(
            answer=text.answer,
            data_row=DataRow(id=data.uid, global_key=data.global_key),
            name=name,
            schema_id=feature_schema_id,
            uuid=uuid,
            message_id=message_id,
            confidence=text.confidence,
            custom_metrics=text.custom_metrics,
        )


class NDChecklist(
    NDAnnotation, NDChecklistSubclass, VideoSupported, _SubclassRegistryBase
):
    @model_serializer(mode="wrap")
    def serialize_model(self, handler):
        res = handler(self)
        if "classifications" in res and res["classifications"] == []:
            del res["classifications"]
        return res

    @classmethod
    def from_common(
        cls,
        uuid: str,
        checklist: Checklist,
        name: str,
        feature_schema_id: Cuid,
        extra: Dict[str, Any],
        data: Union[VideoData, TextData, ImageData],
        message_id: str,
        confidence: Optional[float] = None,
        custom_metrics: Optional[List[CustomMetric]] = None,
    ) -> "NDChecklist":
        return cls(
            answer=[
                NDAnswer(
                    name=answer.name,
                    schema_id=answer.feature_schema_id,
                    confidence=answer.confidence,
                    classifications=[
                        NDSubclassification.from_common(annot)
                        for annot in answer.classifications
                    ]
                    if answer.classifications
                    else None,
                    custom_metrics=answer.custom_metrics,
                )
                for answer in checklist.answer
            ],
            data_row=DataRow(id=data.uid, global_key=data.global_key),
            name=name,
            schema_id=feature_schema_id,
            uuid=uuid,
            frames=extra.get("frames"),
            message_id=message_id,
            confidence=confidence,
        )


class NDRadio(
    NDAnnotation, NDRadioSubclass, VideoSupported, _SubclassRegistryBase
):
    @classmethod
    def from_common(
        cls,
        uuid: str,
        radio: Radio,
        name: str,
        feature_schema_id: Cuid,
        extra: Dict[str, Any],
        data: Union[VideoData, TextData, ImageData],
        message_id: str,
        confidence: Optional[float] = None,
    ) -> "NDRadio":
        return cls(
            answer=NDAnswer(
                name=radio.answer.name,
                schema_id=radio.answer.feature_schema_id,
                confidence=radio.answer.confidence,
                classifications=[
                    NDSubclassification.from_common(annot)
                    for annot in radio.answer.classifications
                ]
                if radio.answer.classifications
                else None,
                custom_metrics=radio.answer.custom_metrics,
            ),
            data_row=DataRow(id=data.uid, global_key=data.global_key),
            name=name,
            schema_id=feature_schema_id,
            uuid=uuid,
            frames=extra.get("frames"),
            message_id=message_id,
            confidence=confidence,
        )

    @model_serializer(mode="wrap")
    def serialize_model(self, handler):
        res = handler(self)
        if "classifications" in res and res["classifications"] == []:
            del res["classifications"]
        return res


class NDPromptText(NDAnnotation, NDPromptTextSubclass, _SubclassRegistryBase):
    @classmethod
    def from_common(
        cls,
        uuid: str,
        text: PromptText,
        name,
        data: Dict,
        feature_schema_id: Cuid,
        confidence: Optional[float] = None,
    ) -> "NDPromptText":
        return cls(
            answer=text.answer,
            data_row=DataRow(id=data.uid, global_key=data.global_key),
            name=name,
            schema_id=feature_schema_id,
            uuid=uuid,
            confidence=text.confidence,
            custom_metrics=text.custom_metrics,
        )


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
        return classify_obj.from_common(
            annotation.value, annotation.name, annotation.feature_schema_id
        )

    @staticmethod
    def to_common(
        annotation: "NDClassificationType",
    ) -> ClassificationAnnotation:
        return ClassificationAnnotation(
            value=annotation.to_common(),
            name=annotation.name,
            feature_schema_id=annotation.schema_id,
        )

    @staticmethod
    def lookup_subclassification(
        annotation: ClassificationAnnotation,
    ) -> Union[NDTextSubclass, NDChecklistSubclass, NDRadioSubclass]:
        return {
            Text: NDTextSubclass,
            Checklist: NDChecklistSubclass,
            Radio: NDRadioSubclass,
        }.get(type(annotation.value))


class NDClassification:
    @staticmethod
    def to_common(
        annotation: "NDClassificationType",
    ) -> Union[ClassificationAnnotation, VideoClassificationAnnotation]:
        common = ClassificationAnnotation(
            value=annotation.to_common(),
            name=annotation.name,
            feature_schema_id=annotation.schema_id,
            extra={"uuid": annotation.uuid},
            message_id=annotation.message_id,
            confidence=annotation.confidence,
        )

        if getattr(annotation, "frames", None) is None:
            return [common]
        results = []
        for frame in annotation.frames:
            for idx in range(frame.start, frame.end + 1, 1):
                results.append(
                    VideoClassificationAnnotation(
                        frame=idx, **common.model_dump(exclude_none=True)
                    )
                )
        return results

    @classmethod
    def from_common(
        cls,
        annotation: Union[
            ClassificationAnnotation, VideoClassificationAnnotation
        ],
        data: Union[VideoData, TextData, ImageData],
    ) -> Union[NDTextSubclass, NDChecklistSubclass, NDRadioSubclass]:
        classify_obj = cls.lookup_classification(annotation)
        if classify_obj is None:
            raise TypeError(
                f"Unable to convert object to MAL format. `{type(annotation.value)}`"
            )
        return classify_obj.from_common(
            str(annotation._uuid),
            annotation.value,
            annotation.name,
            annotation.feature_schema_id,
            annotation.extra,
            data,
            annotation.message_id,
            annotation.confidence,
        )

    @staticmethod
    def lookup_classification(
        annotation: Union[
            ClassificationAnnotation, VideoClassificationAnnotation
        ],
    ) -> Union[NDText, NDChecklist, NDRadio]:
        return {Text: NDText, Checklist: NDChecklist, Radio: NDRadio}.get(
            type(annotation.value)
        )


class NDPromptClassification:
    @staticmethod
    def to_common(
        annotation: "NDPromptClassificationType",
    ) -> Union[PromptClassificationAnnotation]:
        common = PromptClassificationAnnotation(
            value=annotation,
            name=annotation.name,
            feature_schema_id=annotation.schema_id,
            extra={"uuid": annotation.uuid},
            confidence=annotation.confidence,
        )

        return common

    @classmethod
    def from_common(
        cls,
        annotation: Union[PromptClassificationAnnotation],
        data: Union[VideoData, TextData, ImageData],
    ) -> Union[NDTextSubclass, NDChecklistSubclass, NDRadioSubclass]:
        return NDPromptText.from_common(
            str(annotation._uuid),
            annotation.value,
            annotation.name,
            data,
            annotation.feature_schema_id,
            annotation.confidence,
        )


# Make sure to keep NDChecklistSubclass prior to NDRadioSubclass in the list,
# otherwise list of answers gets parsed by NDRadio whereas NDChecklist must be used
NDSubclassificationType = Union[
    NDChecklistSubclass, NDRadioSubclass, NDTextSubclass
]

NDAnswer.model_rebuild()
NDChecklistSubclass.model_rebuild()
NDChecklist.model_rebuild()
NDRadioSubclass.model_rebuild()
NDRadio.model_rebuild()
NDText.model_rebuild()
NDPromptText.model_rebuild()
NDTextSubclass.model_rebuild()

# Make sure to keep NDChecklist prior to NDRadio in the list,
# otherwise list of answers gets parsed by NDRadio whereas NDChecklist must be used
NDClassificationType = Union[NDChecklist, NDRadio, NDText]
NDPromptClassificationType = Union[NDPromptText]
