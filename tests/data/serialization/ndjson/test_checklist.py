import json
from labelbox.data.annotation_types.annotation import ClassificationAnnotation
from labelbox.data.annotation_types.classification.classification import Checklist, ClassificationAnswer, Radio
from labelbox.data.annotation_types.data.text import TextData
from labelbox.data.annotation_types.label import Label

from labelbox.data.serialization.ndjson.converter import NDJsonConverter


def test_serialization():
    label = Label(uid="ckj7z2q0b0000jx6x0q2q7q0d",
                  data=TextData(
                      uid="bkj7z2q0b0000jx6x0q2q7q0d",
                      text="This is a test",
                  ),
                  annotations=[
                      ClassificationAnnotation(
                          name="checkbox_question_geo",
                          confidence=0.5,
                          value=Checklist(answer=[
                              ClassificationAnswer(name="first_answer"),
                              ClassificationAnswer(name="second_answer")
                          ]))
                  ])

    serialized = NDJsonConverter.serialize([label])

    res = next(serialized)
    assert res['confidence'] == 0.5
    assert res['name'] == "checkbox_question_geo"
    assert res['answer'][0]['name'] == "first_answer"
    assert res['answer'][1]['name'] == "second_answer"
    assert res['dataRow']['id'] == "bkj7z2q0b0000jx6x0q2q7q0d"

    deserialized = NDJsonConverter.deserialize([res])
    res = next(deserialized)
    annotation = res.annotations[0]
    assert annotation.confidence == 0.5

    annotation_value = annotation.value
    assert type(annotation_value) is Checklist
    assert annotation_value.answer[0].name == "first_answer"
    assert annotation_value.answer[1].name == "second_answer"
