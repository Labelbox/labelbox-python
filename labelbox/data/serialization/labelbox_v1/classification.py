from typing import List, Union

from pydantic.main import BaseModel

from ...annotation_types.annotation import ClassificationAnnotation
from ...annotation_types.classification import Checklist, ClassificationAnswer, Radio, Text, Dropdown
from ...annotation_types.types import Cuid
from .feature import LBV1Feature


class LBV1ClassificationAnswer(LBV1Feature):
    ...


class LBV1Radio(LBV1Feature):
    answer: LBV1ClassificationAnswer

    def to_common(self):
        return Radio(answer=ClassificationAnswer(
            feature_schema_id=self.answer.schema_id,
            name=self.answer.title,
            extra={
                'feature_id': self.answer.feature_id,
                'value': self.answer.value
            }))

    @classmethod
    def from_common(cls, radio: Radio, feature_schema_id: Cuid,
                    **extra) -> "LBV1Radio":
        return cls(schema_id=feature_schema_id,
                   answer=LBV1ClassificationAnswer(
                       schema_id=radio.answer.feature_schema_id,
                       title=radio.answer.name,
                       value=radio.answer.extra.get('value'),
                       feature_id=radio.answer.extra.get('feature_id')),
                   **extra)


class LBV1Checklist(LBV1Feature):
    answers: List[LBV1ClassificationAnswer]

    def to_common(self):
        return Checklist(answer=[
            ClassificationAnswer(feature_schema_id=answer.schema_id,
                                 name=answer.title,
                                 extra={
                                     'feature_id': answer.feature_id,
                                     'value': answer.value
                                 }) for answer in self.answers
        ])

    @classmethod
    def from_common(cls, checklist: Checklist, feature_schema_id: Cuid,
                    **extra) -> "LBV1Checklist":
        return cls(schema_id=feature_schema_id,
                   answers=[
                       LBV1ClassificationAnswer(
                           schema_id=answer.feature_schema_id,
                           title=answer.name,
                           value=answer.extra.get('value'),
                           feature_id=answer.extra.get('feature_id'))
                       for answer in checklist.answer
                   ],
                   **extra)


class LBV1Text(LBV1Feature):
    answer: str

    def to_common(self):
        return Text(answer=self.answer)

    @classmethod
    def from_common(cls, text: Text, feature_schema_id: Cuid,
                    **extra) -> "LBV1Text":
        return cls(schema_id=feature_schema_id, answer=text.answer, **extra)


class LBV1Classifications(BaseModel):
    classifications: List[Union[LBV1Radio, LBV1Checklist, LBV1Text]] = []

    def to_common(self) -> List[ClassificationAnnotation]:
        classifications = [
            ClassificationAnnotation(value=classification.to_common(),
                                     classifications=[],
                                     name=classification.title,
                                     feature_schema_id=classification.schema_id,
                                     extra={
                                         'value': classification.value,
                                         'feature_id': classification.feature_id
                                     })
            for classification in self.classifications
        ]
        return classifications

    @classmethod
    def from_common(
            cls, annotations: List[ClassificationAnnotation]
    ) -> "LBV1Classifications":
        classifications = []
        for annotation in annotations:
            classification = cls.lookup_classification(annotation)
            if classification is not None:
                classifications.append(
                    classification.from_common(annotation.value,
                                               annotation.feature_schema_id,
                                               **annotation.extra))
            else:
                raise TypeError(f"Unexpected type {type(annotation.value)}")
        return cls(classifications=classifications)

    @staticmethod
    def lookup_classification(
        annotation: ClassificationAnnotation
    ) -> Union[LBV1Text, LBV1Checklist, LBV1Radio]:
        return {
            Text: LBV1Text,
            Dropdown: LBV1Checklist,
            Checklist: LBV1Checklist,
            Radio: LBV1Radio
        }.get(type(annotation.value))
