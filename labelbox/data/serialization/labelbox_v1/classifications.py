from typing import List

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
            schema_id=self.answer.schema_id, display_name=self.answer.value, alternative_name = self.answer.title, extra = {'feature_id' :  self.answer.feature_id}))

    @classmethod
    def from_common(cls, radio : Radio, schema_id: str, **extra) -> "LBV1Radio":
        return cls(
            # TODO: Get the right order for alternative name and display name
            schema_id = schema_id,
            answer = LBV1ClassificationAnswer(schema_id = radio.answer.schema_id, title = radio.answer.alternative_name, value = radio.answer.display_name, feature_id = radio.answer.extra['feature_id']),
            **extra
        )


class LBV1Checklist(LBV1Feature):
    answers: List[LBV1ClassificationAnswer]

    def to_common(self):
        return CheckList(answer=[
            ClassificationAnswer(schema_id=answer.schema_id,
                                 display_name=answer.value)
            for answer in self.answers
        ])

    @classmethod
    def from_common(cls, checklist : CheckList, schema_id: str, **extra) -> "LBV1Checklist":
        return cls(
            # TODO: Get the right order for alternative name and display name
            schema_id = schema_id,
            answers = [LBV1ClassificationAnswer(schema_id = answer.schema_id, title = answer.alternative_name, value = answer.display_name) for answer in checklist.answer],
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

