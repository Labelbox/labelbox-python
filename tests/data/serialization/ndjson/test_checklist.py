from labelbox.data.annotation_types.annotation import ClassificationAnnotation
from labelbox.data.annotation_types.classification.classification import Checklist, ClassificationAnswer, Radio
from labelbox.data.annotation_types.data.text import TextData
from labelbox.data.annotation_types.label import Label

from labelbox.data.serialization.ndjson.converter import NDJsonConverter


def test_serialization_min():
    label = Label(
        uid="ckj7z2q0b0000jx6x0q2q7q0d",
        data=TextData(
            uid="bkj7z2q0b0000jx6x0q2q7q0d",
            text="This is a test",
        ),
        annotations=[
            ClassificationAnnotation(
                name="checkbox_question_geo",
                value=Checklist(
                    answer=[ClassificationAnswer(name="first_answer")]),
            )
        ])

    serialized = NDJsonConverter.serialize([label])
    res = next(serialized)

    assert res['name'] == "checkbox_question_geo"
    assert res['dataRow']['id'] == "bkj7z2q0b0000jx6x0q2q7q0d"

    first_answer = res['answer'][0]
    assert first_answer['name'] == "first_answer"
    classifications = first_answer.get('classifications')
    assert classifications is None

    deserialized = NDJsonConverter.deserialize([res])
    res = next(deserialized)
    annotation = res.annotations[0]

    annotation_value = annotation.value
    assert type(annotation_value) is Checklist
    annotaion_answer = annotation_value.answer[0]
    assert annotaion_answer.name == "first_answer"


def test_serialization_with_classification():
    label = Label(
        uid="ckj7z2q0b0000jx6x0q2q7q0d",
        data=TextData(
            uid="bkj7z2q0b0000jx6x0q2q7q0d",
            text="This is a test",
        ),
        annotations=[
            ClassificationAnnotation(
                name="checkbox_question_geo",
                confidence=0.5,
                value=Checklist(answer=[
                    ClassificationAnswer(
                        name="first_answer",
                        confidence=0.1,
                        classifications=[
                            ClassificationAnnotation(
                                name="sub_radio_question",
                                value=Radio(answer=ClassificationAnswer(
                                    name="first_sub_radio_answer",
                                    confidence=0.31))),
                            ClassificationAnnotation(
                                name="sub_chck_question",
                                value=Checklist(answer=[
                                    ClassificationAnswer(
                                        name="second_subchk_answer",
                                        confidence=0.41),
                                    ClassificationAnswer(
                                        name="third_subchk_answer",
                                        confidence=0.42),
                                ],))
                        ]),
                ]))
        ])

    serialized = NDJsonConverter.serialize([label])
    res = next(serialized)

    assert res['confidence'] == 0.5
    assert res['name'] == "checkbox_question_geo"
    assert res['dataRow']['id'] == "bkj7z2q0b0000jx6x0q2q7q0d"

    first_answer = res['answer'][0]
    assert first_answer['name'] == "first_answer"
    assert first_answer['confidence'] == 0.1
    classifications = first_answer['classifications']
    assert len(classifications) == 2
    assert classifications[0]['name'] == "sub_radio_question"
    assert classifications[0]['answer']['name'] == "first_sub_radio_answer"
    assert classifications[0]['answer']['confidence'] == 0.31
    assert classifications[1]['name'] == "sub_chck_question"
    assert classifications[1]['answer'][0]['name'] == "second_subchk_answer"
    assert classifications[1]['answer'][0]['confidence'] == 0.41
    assert classifications[1]['answer'][1]['name'] == "third_subchk_answer"
    assert classifications[1]['answer'][1]['confidence'] == 0.42

    deserialized = NDJsonConverter.deserialize([res])
    res = next(deserialized)
    annotation = res.annotations[0]
    assert annotation.confidence == 0.5

    annotation_value = annotation.value
    assert type(annotation_value) is Checklist
    annotaion_answer = annotation_value.answer[0]
    assert annotaion_answer.name == "first_answer"
    assert annotaion_answer.confidence == 0.1
    classifications = annotaion_answer.classifications
    assert len(classifications) == 2
    classification_types = [type(c.value) for c in classifications]
    assert classification_types == [Radio, Checklist]
    answers = [
        classifications[0].value.answer, classifications[1].value.answer[0],
        classifications[1].value.answer[1]
    ]
    assert [a.name for a in answers] == [
        "first_sub_radio_answer", "second_subchk_answer", "third_subchk_answer"
    ]
    assert [a.confidence for a in answers] == [0.31, 0.41, 0.42]


def test_serialization_with_classification_double_nested():
    label = Label(
        uid="ckj7z2q0b0000jx6x0q2q7q0d",
        data=TextData(
            uid="bkj7z2q0b0000jx6x0q2q7q0d",
            text="This is a test",
        ),
        annotations=[
            ClassificationAnnotation(
                name="checkbox_question_geo",
                confidence=0.5,
                value=Checklist(answer=[
                    ClassificationAnswer(
                        name="first_answer",
                        confidence=0.1,
                        classifications=[
                            ClassificationAnnotation(
                                name="sub_radio_question",
                                value=Radio(answer=ClassificationAnswer(
                                    name="first_sub_radio_answer",
                                    confidence=0.31,
                                    classifications=[
                                        ClassificationAnnotation(
                                            name="sub_chck_question",
                                            value=Checklist(answer=[
                                                ClassificationAnswer(
                                                    name="second_subchk_answer",
                                                    confidence=0.41),
                                                ClassificationAnswer(
                                                    name="third_subchk_answer",
                                                    confidence=0.42),
                                            ],))
                                    ]))),
                        ]),
                ]))
        ])

    expected = {
        'confidence':
            0.5,
        'name':
            'checkbox_question_geo',
        'dataRow': {
            'id': 'bkj7z2q0b0000jx6x0q2q7q0d'
        },
        'answer': [{
            'confidence':
                0.1,
            'name':
                'first_answer',
            'classifications': [{
                'name': 'sub_radio_question',
                'schema_id': None,
                'answer': {
                    'confidence':
                        0.31,
                    'name':
                        'first_sub_radio_answer',
                    'schema_id':
                        None,
                    'classifications': [{
                        'name':
                            'sub_chck_question',
                        'schema_id':
                            None,
                        'answer': [{
                            'confidence': 0.41,
                            'name': 'second_subchk_answer',
                            'schema_id': None
                        }, {
                            'confidence': 0.42,
                            'name': 'third_subchk_answer',
                            'schema_id': None
                        }]
                    }]
                }
            }]
        }]
    }
    serialized = NDJsonConverter.serialize([label])
    res = next(serialized)

    res.pop("uuid")
    assert res == expected

    deserialized = NDJsonConverter.deserialize([res])
    res = next(deserialized)
    res.annotations[0].extra.pop("uuid")
    assert res.annotations == label.annotations


def test_serialization_with_classification_double_nested_2():
    label = Label(
        uid="ckj7z2q0b0000jx6x0q2q7q0d",
        data=TextData(
            uid="bkj7z2q0b0000jx6x0q2q7q0d",
            text="This is a test",
        ),
        annotations=[
            ClassificationAnnotation(
                name="sub_radio_question",
                value=Radio(answer=ClassificationAnswer(
                    name="first_sub_radio_answer",
                    confidence=0.31,
                    classifications=[
                        ClassificationAnnotation(
                            name="sub_chck_question",
                            value=Checklist(answer=[
                                ClassificationAnswer(
                                    name="second_subchk_answer",
                                    confidence=0.41,
                                    classifications=[
                                        ClassificationAnnotation(
                                            name="checkbox_question_geo",
                                            value=Checklist(answer=[
                                                ClassificationAnswer(
                                                    name="first_answer",
                                                    confidence=0.1,
                                                    classifications=[]),
                                            ]))
                                    ]),
                                ClassificationAnswer(name="third_subchk_answer",
                                                     confidence=0.42),
                            ]))
                    ]))),
        ])

    expected = {
        'name': 'sub_radio_question',
        'answer': {
            'confidence':
                0.31,
            'name':
                'first_sub_radio_answer',
            'classifications': [{
                'name':
                    'sub_chck_question',
                'schema_id':
                    None,
                'answer': [{
                    'confidence':
                        0.41,
                    'name':
                        'second_subchk_answer',
                    'schema_id':
                        None,
                    'classifications': [{
                        'name':
                            'checkbox_question_geo',
                        'schema_id':
                            None,
                        'answer': [{
                            'confidence': 0.1,
                            'name': 'first_answer',
                            'schema_id': None
                        }]
                    }]
                }, {
                    'confidence': 0.42,
                    'name': 'third_subchk_answer',
                    'schema_id': None
                }]
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
