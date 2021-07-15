from typing import List

from labelbox.data.serialization.labelbox_v1.feature import LBV1Feature
from labelbox.data.annotation_types.classification import Text, Radio, CheckList, ClassificationAnswer


class LBV1ClassificationAnswer(LBV1Feature):
    ...


class LBV1Radio(LBV1Feature):
    answer: LBV1ClassificationAnswer

    def to_common(self):
        return Radio(answer=ClassificationAnswer(
            schema_id=self.answer.schemaId, display_name=self.answer.value))


class LBV1Checklist(LBV1Feature):
    answers: List[LBV1ClassificationAnswer]

    def to_common(self):
        return CheckList(answer=[
            ClassificationAnswer(schema_id=answer.schemaId,
                                 display_name=answer.value)
            for answer in self.answers
        ])


class LBV1Text(LBV1Feature):
    answer: str

    def to_common(self):
        return Text(answer=self.answer)


