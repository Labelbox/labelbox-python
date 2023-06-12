from labelbox.data.annotation_types.annotation import ClassificationAnnotation
from labelbox.data.annotation_types.classification.classification import ClassificationAnswer, Radio, Text
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
                          name="radio_question_geo",
                          confidence=0.5,
                          value=Text(answer="first_radio_answer"))
                  ])

    serialized = NDJsonConverter.serialize([label])
    res = next(serialized)
    assert 'confidence' not in res  # because confidence needs to be set on the annotation itself
    assert res['name'] == "radio_question_geo"
    assert res['answer'] == "first_radio_answer"
    assert res['dataRow']['id'] == "bkj7z2q0b0000jx6x0q2q7q0d"

    deserialized = NDJsonConverter.deserialize([res])
    res = next(deserialized)
    annotation = res.annotations[0]

    annotation_value = annotation.value
    assert type(annotation_value) is Text
    assert annotation_value.answer == "first_radio_answer"
