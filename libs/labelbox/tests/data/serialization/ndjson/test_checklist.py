from labelbox.data.annotation_types.annotation import ClassificationAnnotation
from labelbox.data.annotation_types.classification.classification import (
    Checklist,
    ClassificationAnswer,
    Radio,
)
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
                    answer=[ClassificationAnswer(name="first_answer")]
                ),
            )
        ],
    )

    expected = {
        "name": "checkbox_question_geo",
        "dataRow": {"id": "bkj7z2q0b0000jx6x0q2q7q0d"},
        "answer": [{"name": "first_answer"}],
    }
    serialized = NDJsonConverter.serialize([label])
    res = next(serialized)
    res.pop("uuid")
    assert res == expected

    deserialized = NDJsonConverter.deserialize([res])
    res = next(deserialized)
    for i, annotation in enumerate(res.annotations):
        annotation.extra.pop("uuid")
        assert annotation.value == label.annotations[i].value
        assert annotation.name == label.annotations[i].name


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
                value=Checklist(
                    answer=[
                        ClassificationAnswer(
                            name="first_answer",
                            confidence=0.1,
                            classifications=[
                                ClassificationAnnotation(
                                    name="sub_radio_question",
                                    value=Radio(
                                        answer=ClassificationAnswer(
                                            name="first_sub_radio_answer",
                                            confidence=0.31,
                                        )
                                    ),
                                ),
                                ClassificationAnnotation(
                                    name="sub_chck_question",
                                    value=Checklist(
                                        answer=[
                                            ClassificationAnswer(
                                                name="second_subchk_answer",
                                                confidence=0.41,
                                            ),
                                            ClassificationAnswer(
                                                name="third_subchk_answer",
                                                confidence=0.42,
                                            ),
                                        ],
                                    ),
                                ),
                            ],
                        ),
                    ]
                ),
            )
        ],
    )

    expected = {
        "confidence": 0.5,
        "name": "checkbox_question_geo",
        "dataRow": {"id": "bkj7z2q0b0000jx6x0q2q7q0d"},
        "answer": [
            {
                "confidence": 0.1,
                "name": "first_answer",
                "classifications": [
                    {
                        "name": "sub_radio_question",
                        "answer": {
                            "confidence": 0.31,
                            "name": "first_sub_radio_answer",
                        },
                    },
                    {
                        "name": "sub_chck_question",
                        "answer": [
                            {
                                "confidence": 0.41,
                                "name": "second_subchk_answer",
                            },
                            {
                                "confidence": 0.42,
                                "name": "third_subchk_answer",
                            },
                        ],
                    },
                ],
            }
        ],
    }

    serialized = NDJsonConverter.serialize([label])
    res = next(serialized)

    res.pop("uuid")
    assert res == expected

    deserialized = NDJsonConverter.deserialize([res])
    res = next(deserialized)
    assert label.model_dump(exclude_none=True) == label.model_dump(
        exclude_none=True
    )


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
                value=Checklist(
                    answer=[
                        ClassificationAnswer(
                            name="first_answer",
                            confidence=0.1,
                            classifications=[
                                ClassificationAnnotation(
                                    name="sub_radio_question",
                                    value=Radio(
                                        answer=ClassificationAnswer(
                                            name="first_sub_radio_answer",
                                            confidence=0.31,
                                            classifications=[
                                                ClassificationAnnotation(
                                                    name="sub_chck_question",
                                                    value=Checklist(
                                                        answer=[
                                                            ClassificationAnswer(
                                                                name="second_subchk_answer",
                                                                confidence=0.41,
                                                            ),
                                                            ClassificationAnswer(
                                                                name="third_subchk_answer",
                                                                confidence=0.42,
                                                            ),
                                                        ],
                                                    ),
                                                )
                                            ],
                                        )
                                    ),
                                ),
                            ],
                        ),
                    ]
                ),
            )
        ],
    )

    expected = {
        "confidence": 0.5,
        "name": "checkbox_question_geo",
        "dataRow": {"id": "bkj7z2q0b0000jx6x0q2q7q0d"},
        "answer": [
            {
                "confidence": 0.1,
                "name": "first_answer",
                "classifications": [
                    {
                        "name": "sub_radio_question",
                        "answer": {
                            "confidence": 0.31,
                            "name": "first_sub_radio_answer",
                            "classifications": [
                                {
                                    "name": "sub_chck_question",
                                    "answer": [
                                        {
                                            "confidence": 0.41,
                                            "name": "second_subchk_answer",
                                        },
                                        {
                                            "confidence": 0.42,
                                            "name": "third_subchk_answer",
                                        },
                                    ],
                                }
                            ],
                        },
                    }
                ],
            }
        ],
    }
    serialized = NDJsonConverter.serialize([label])
    res = next(serialized)

    res.pop("uuid")
    assert res == expected

    deserialized = NDJsonConverter.deserialize([res])
    res = next(deserialized)
    res.annotations[0].extra.pop("uuid")
    assert label.model_dump(exclude_none=True) == label.model_dump(
        exclude_none=True
    )


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
                value=Radio(
                    answer=ClassificationAnswer(
                        name="first_sub_radio_answer",
                        confidence=0.31,
                        classifications=[
                            ClassificationAnnotation(
                                name="sub_chck_question",
                                value=Checklist(
                                    answer=[
                                        ClassificationAnswer(
                                            name="second_subchk_answer",
                                            confidence=0.41,
                                            classifications=[
                                                ClassificationAnnotation(
                                                    name="checkbox_question_geo",
                                                    value=Checklist(
                                                        answer=[
                                                            ClassificationAnswer(
                                                                name="first_answer",
                                                                confidence=0.1,
                                                            ),
                                                        ]
                                                    ),
                                                )
                                            ],
                                        ),
                                        ClassificationAnswer(
                                            name="third_subchk_answer",
                                            confidence=0.42,
                                        ),
                                    ]
                                ),
                            )
                        ],
                    )
                ),
            ),
        ],
    )

    expected = {
        "name": "sub_radio_question",
        "answer": {
            "confidence": 0.31,
            "name": "first_sub_radio_answer",
            "classifications": [
                {
                    "name": "sub_chck_question",
                    "answer": [
                        {
                            "confidence": 0.41,
                            "name": "second_subchk_answer",
                            "classifications": [
                                {
                                    "name": "checkbox_question_geo",
                                    "answer": [
                                        {
                                            "confidence": 0.1,
                                            "name": "first_answer",
                                        }
                                    ],
                                }
                            ],
                        },
                        {
                            "confidence": 0.42,
                            "name": "third_subchk_answer",
                        },
                    ],
                }
            ],
        },
        "dataRow": {"id": "bkj7z2q0b0000jx6x0q2q7q0d"},
    }

    serialized = NDJsonConverter.serialize([label])
    res = next(serialized)
    res.pop("uuid")
    assert res == expected

    deserialized = NDJsonConverter.deserialize([res])
    res = next(deserialized)
    assert label.model_dump(exclude_none=True) == label.model_dump(
        exclude_none=True
    )
