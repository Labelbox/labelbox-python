from typing import List, Union

from pydantic.main import BaseModel

from .feature import LBV1Feature
from ...annotation_types.annotation import ClassificationAnnotation
from ...annotation_types.classification import Checklist, ClassificationAnswer, Radio, Text, Dropdown
from ...annotation_types.types import Cuid


class LBV1ClassificationAnswer(LBV1Feature):

    def to_common(self) -> ClassificationAnswer:
        return ClassificationAnswer(feature_schema_id=self.schema_id,
                                    name=self.title,
                                    keyframe=self.keyframe,
                                    extra={
                                        'feature_id': self.feature_id,
                                        'value': self.value
                                    })

    @classmethod
    def from_common(
            cls,
            answer: ClassificationAnnotation) -> "LBV1ClassificationAnswer":
        return cls(schema_id=answer.feature_schema_id,
                   title=answer.name,
                   value=answer.extra.get('value'),
                   feature_id=answer.extra.get('feature_id'),
                   keyframe=answer.keyframe)


class LBV1Radio(LBV1Feature):
    answer: LBV1ClassificationAnswer

    def to_common(self) -> Radio:
        return Radio(answer=self.answer.to_common())

    @classmethod
    def from_common(cls, radio: Radio, feature_schema_id: Cuid,
                    **extra) -> "LBV1Radio":
        return cls(schema_id=feature_schema_id,
                   answer=LBV1ClassificationAnswer.from_common(radio.answer),
                   **extra)


class LBV1Checklist(LBV1Feature):
    answers: List[LBV1ClassificationAnswer]

    def to_common(self) -> Checklist:
        return Checklist(answer=[answer.to_common() for answer in self.answers])

    @classmethod
    def from_common(cls, checklist: Checklist, feature_schema_id: Cuid,
                    **extra) -> "LBV1Checklist":
        return cls(schema_id=feature_schema_id,
                   answers=[
                       LBV1ClassificationAnswer.from_common(answer)
                       for answer in checklist.answer
                   ],
                   **extra)


class LBV1Dropdown(LBV1Feature):
    answer: List[LBV1ClassificationAnswer]

    def to_common(self) -> Dropdown:
        return Dropdown(answer=[answer.to_common() for answer in self.answer])

    @classmethod
    def from_common(cls, dropdown: Dropdown, feature_schema_id: Cuid,
                    **extra) -> "LBV1Dropdown":
        return cls(schema_id=feature_schema_id,
                   answer=[
                       LBV1ClassificationAnswer.from_common(answer)
                       for answer in dropdown.answer
                   ],
                   **extra)


class LBV1Text(LBV1Feature):
    answer: str

    def to_common(self) -> Text:
        return Text(answer=self.answer)

    @classmethod
    def from_common(cls, text: Text, feature_schema_id: Cuid,
                    **extra) -> "LBV1Text":
        return cls(schema_id=feature_schema_id, answer=text.answer, **extra)


class LBV1Classifications(BaseModel):
    classifications: List[Union[LBV1Text, LBV1Radio, LBV1Dropdown,
                                LBV1Checklist]] = []

    def to_common(self) -> List[ClassificationAnnotation]:
        classifications = [
            ClassificationAnnotation(value=classification.to_common(),
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
    ) -> Union[LBV1Text, LBV1Checklist, LBV1Radio, LBV1Checklist]:
        return {
            Text: LBV1Text,
            Dropdown: LBV1Dropdown,
            Checklist: LBV1Checklist,
            Radio: LBV1Radio
        }.get(type(annotation.value))
