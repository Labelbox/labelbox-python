import json
from labelbox.data.annotation_types.annotation import ClassificationAnnotation
from labelbox.data.annotation_types.classification.classification import ClassificationAnswer
from labelbox.data.annotation_types.classification.classification import Radio
from labelbox.data.annotation_types.data.text import TextData
from labelbox.data.annotation_types.label import Label

from labelbox.data.serialization.ndjson.converter import NDJsonConverter


def test_serialization_with_radio_min():
    label = Label(
        uid="ckj7z2q0b0000jx6x0q2q7q0d",
        data=TextData(
            uid="bkj7z2q0b0000jx6x0q2q7q0d",
            text="This is a test",
        ),
        annotations=[
            ClassificationAnnotation(
                name="radio_question_geo",
                value=Radio(
                    answer=ClassificationAnswer(name="first_radio_answer",)))
        ])

    expected = {
        'name': 'radio_question_geo',
        'answer': {
            'name': 'first_radio_answer'
        },
        'dataRow': {
            'id': 'bkj7z2q0b0000jx6x0q2q7q0d'
        }
    }
    serialized = NDJsonConverter.serialize([label])
    res = next(serialized)

    res.pop("uuid")
    assert res == expected

    deserialized = NDJsonConverter.deserialize([res])
    res = next(deserialized)
    res.annotations[0].extra.pop("uuid")
    assert res.annotations == label.annotations


def test_serialization_with_radio_classification():
    label = Label(uid="ckj7z2q0b0000jx6x0q2q7q0d",
                  data=TextData(
                      uid="bkj7z2q0b0000jx6x0q2q7q0d",
                      text="This is a test",
                  ),
                  annotations=[
                      ClassificationAnnotation(
                          name="radio_question_geo",
                          confidence=0.5,
                          value=Radio(answer=ClassificationAnswer(
                              confidence=0.6,
                              name="first_radio_answer",
                              classifications=[
                                  ClassificationAnnotation(
                                      name="sub_radio_question",
                                      value=Radio(answer=ClassificationAnswer(
                                          name="first_sub_radio_answer")))
                              ])))
                  ])

    expected = {
        'confidence': 0.5,
        'name': 'radio_question_geo',
        'answer': {
            'confidence':
                0.6,
            'name':
                'first_radio_answer',
            'classifications': [{
                'name': 'sub_radio_question',
                'answer': {
                    'name': 'first_sub_radio_answer',
                }
            }]
        },
        'dataRow': {
            'id': 'bkj7z2q0b0000jx6x0q2q7q0d'
        }
    }

    serialized = NDJsonConverter.serialize([label])
    res = next(serialized)
    res.pop("uuid")
    assert res == expected

    deserialized = NDJsonConverter.deserialize([res])
    res = next(deserialized)
    res.annotations[0].extra.pop("uuid")
    assert res.annotations == label.annotations
