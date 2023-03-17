from typing import Any, Dict, List, Union

from pydantic import Field
from labelbox.data.serialization.ndjson.nd_feature import NDFeature

from ...annotation_types.classification.classification import ClassificationAnswer, Checklist
from ...annotation_types.types import Cuid
from ...annotation_types.data import TextData, VideoData, ImageData
from .data_row import DataRow
from .annotation import NDAnnotation

from typing import Any, Dict, List, Union

from labelbox.data.serialization.ndjson.nd_feature import NDFeature
from labelbox.data.serialization.ndjson.objects import NDBaseObject

from ...annotation_types.annotation import ClassificationAnnotation
from ...annotation_types.classification.classification import Text
from ...annotation_types.types import Cuid
from ...annotation_types.data import TextData, ImageData
from .base import DataRow


class NDChecklistSubclass(NDFeature):
    answer: List[NDFeature] = Field(..., alias='answers')

    def to_common(self) -> Checklist:
        return Checklist(answer=[
            ClassificationAnswer(name=answer.name,
                                 feature_schema_id=answer.schema_id,
                                 confidence=answer.confidence)
            for answer in self.answer
        ])

    @classmethod
    def from_common(cls, checklist: Checklist, name: str,
                    feature_schema_id: Cuid) -> "NDChecklistSubclass":
        return cls(answer=[
            NDFeature(name=answer.name,
                      schema_id=answer.feature_schema_id,
                      confidence=answer.confidence)
            for answer in checklist.answer
        ],
                   name=name,
                   schema_id=feature_schema_id)

    def dict(self, *args, **kwargs):
        res = super().dict(*args, **kwargs)
        if 'answers' in res:
            res['answer'] = res.pop('answers')
        return res


class NDChecklist(NDAnnotation, NDChecklistSubclass, VideoSupported):

    @classmethod
    def from_common(
            cls, checklist: Checklist, name: str, feature_schema_id: Cuid,
            extra: Dict[str, Any], data: Union[VideoData, TextData,
                                               ImageData]) -> "NDChecklist":
        return cls(answer=[
            NDFeature(name=answer.name,
                      schema_id=answer.feature_schema_id,
                      confidence=answer.confidence)
            for answer in checklist.answer
        ],
                   data_row=DataRow(id=data.uid, global_key=data.global_key),
                   name=name,
                   schema_id=feature_schema_id,
                   uuid=extra.get('uuid'),
                   frames=extra.get('frames'))
    

class NDTextSubclass(NDFeature):
    answer: str

    def to_common(self) -> Text:
        return Text(answer=self.answer)

    @classmethod
    def from_common(cls, text: Text, name: str,
                    feature_schema_id: Cuid) -> "NDTextSubclass":
        return cls(answer=text.answer, name=name, schema_id=feature_schema_id)


class NDText(NDBaseObject, NDTextSubclass):

    @classmethod
    def from_common(cls, text: Text, classifications: List[ClassificationAnnotation], name: str, feature_schema_id: Cuid,
                    extra: Dict[str, Any], data: Union[TextData,
                                                       ImageData]) -> "NDText":
        return cls(
            answer=text.answer,
            classifications=classifications,
            data_row=DataRow(id=data.uid, global_key=data.global_key),
            name=name,
            schema_id=feature_schema_id,
            uuid=extra.get('uuid'),
        )


class NDRadioSubclass(NDFeature):
    answer: NDFeature

    def to_common(self) -> Radio:
        return Radio(
            answer=ClassificationAnswer(name=self.answer.name,
                                        feature_schema_id=self.answer.schema_id,
                                        confidence=self.answer.confidence))

    @classmethod
    def from_common(cls, radio: Radio, name: str,
                    feature_schema_id: Cuid) -> "NDRadioSubclass":
        return cls(answer=NDFeature(name=radio.answer.name,
                                    schema_id=radio.answer.feature_schema_id,
                                    confidence=radio.answer.confidence),
                   name=name,
                   schema_id=feature_schema_id)


class NDRadio(NDAnnotation, NDRadioSubclass, VideoSupported):

    @classmethod
    def from_common(cls, radio: Radio, name: str, feature_schema_id: Cuid,
                    extra: Dict[str, Any], data: Union[VideoData, TextData,
                                                       ImageData]) -> "NDRadio":
        return cls(answer=NDFeature(name=radio.answer.name,
                                    schema_id=radio.answer.feature_schema_id,
                                    confidence=radio.answer.confidence),
                   data_row=DataRow(id=data.uid, global_key=data.global_key),
                   name=name,
                   schema_id=feature_schema_id,
                   uuid=extra.get('uuid'),
                   frames=extra.get('frames'))



NDSubclassificationType = Union[NDChecklistSubclass, NDRadioSubclass,
                                NDTextSubclass]
