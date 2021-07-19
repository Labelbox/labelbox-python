from labelbox.data.annotation_types.classification.classification import Dropdown
from labelbox.data.annotation_types.annotation import AnnotationType, ClassificationAnnotation
from typing import List, Union
from pydantic.main import BaseModel

from pydantic.schema import schema
from pydantic.typing import display_as_type

from labelbox.data.serialization.labelbox_v1.feature import LBV1Feature
from labelbox.data.annotation_types.classification import Text, Radio, CheckList, ClassificationAnswer


class LBV1ClassificationAnswer(LBV1Feature):
    ...


class LBV1Radio(LBV1Feature):
    answer: LBV1ClassificationAnswer

    def to_common(self):
        return Radio(answer=ClassificationAnswer(
            schema_id=self.answer.schema_id, display_name=self.answer.value, extra = {'feature_id' :  self.answer.feature_id, 'alternative_name' : self.answer.title}))

    @classmethod
    def from_common(cls, radio : Radio, schema_id: str, **extra) -> "LBV1Radio":
        return cls(
            # TODO: Get the right order for alternative name and display name
            schema_id = schema_id,
            answer = LBV1ClassificationAnswer(schema_id = radio.answer.schema_id, title = radio.answer.extra['alternative_name'], value = radio.answer.display_name, feature_id = radio.answer.extra['feature_id']),
            **extra
        )


class LBV1Checklist(LBV1Feature):
    answers: List[LBV1ClassificationAnswer]

    def to_common(self):
        return CheckList(answer=[
            ClassificationAnswer(schema_id=answer.schema_id,
                                 display_name=answer.value, extra = {'feature_id' :  answer.feature_id, 'alternative_name' : answer.title})
            for answer in self.answers
        ])

    @classmethod
    def from_common(cls, checklist : CheckList, schema_id: str, **extra) -> "LBV1Checklist":
        return cls(
            # TODO: Get the right order for alternative name and display name
            schema_id = schema_id,
            answers = [LBV1ClassificationAnswer(schema_id = answer.schema_id, title = answer.extra['alternative_name'], value = answer.display_name, feature_id = answer.extra['feature_id']) for answer in checklist.answer],
            **extra
        )


class LBV1Text(LBV1Feature):
    answer: str

    def to_common(self):
        return Text(answer=self.answer)

    @classmethod
    def from_common(cls, text : Text, schema_id: str, **extra) -> "LBV1Text":
        return cls(
            schema_id = schema_id,
            answer = text.answer,
            **extra
        )


class LBV1Classifications(BaseModel):
    classifications: List[Union[LBV1Radio, LBV1Checklist, LBV1Text]] = []


    @staticmethod
    def lookup_classification(annotation: AnnotationType):
        return {
            Text: LBV1Text,
            Dropdown: LBV1Checklist,
            CheckList: LBV1Checklist,
            Radio: LBV1Radio,
        }.get(type(annotation.value))

    def to_common(self):
        classifications = [
                ClassificationAnnotation(value = classification.to_common(),
                        classifications=[],
                        display_name=classification.title)
                for classification in self.classifications
        ]
        return classifications

    @classmethod
    def from_common(cls, annotations: List[AnnotationType]) -> "LBV1Classifications":
        classifications = []
        for annotation in annotations:
            classification = cls.lookup_classification(annotation)
            if classification is not None:
                classifications.append(
                    classification.from_common(annotation.value, annotation.schema_id, keyframe = getattr(annotation,'keyframe', None), **annotation.extra))
            else:
                raise TypeError(f"Unexpected type {type(annotation.value)}")
        return cls(classifications=classifications)
