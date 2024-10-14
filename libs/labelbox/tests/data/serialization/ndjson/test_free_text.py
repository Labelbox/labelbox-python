from labelbox.data.annotation_types.annotation import ClassificationAnnotation
from labelbox.data.annotation_types.classification.classification import (
    Checklist,
    ClassificationAnswer,
    Radio,
    Text,
)
from labelbox.data.annotation_types.data import GenericDataRowData
from labelbox.data.annotation_types.label import Label

from labelbox.data.serialization.ndjson.converter import NDJsonConverter


def test_serialization():
    label = Label(
        uid="ckj7z2q0b0000jx6x0q2q7q0d",
        data=GenericDataRowData(
            uid="bkj7z2q0b0000jx6x0q2q7q0d",
            text="This is a test",
        ),
        annotations=[
            ClassificationAnnotation(
                name="free_text_annotation",
                value=Text(confidence=0.5, answer="text_answer"),
            )
        ],
    )

    serialized = NDJsonConverter.serialize([label])
    res = next(serialized)

    assert res["confidence"] == 0.5
    assert res["name"] == "free_text_annotation"
    assert res["answer"] == "text_answer"
    assert res["dataRow"]["id"] == "bkj7z2q0b0000jx6x0q2q7q0d"


def test_nested_serialization():
    label = Label(
        uid="ckj7z2q0b0000jx6x0q2q7q0d",
        data=GenericDataRowData(
            uid="bkj7z2q0b0000jx6x0q2q7q0d",
            text="This is a test",
        ),
        annotations=[
            ClassificationAnnotation(
                name="nested test",
                value=Checklist(
                    answer=[
                        ClassificationAnswer(
                            name="first_answer",
                            confidence=0.9,
                            classifications=[
                                ClassificationAnnotation(
                                    name="sub_radio_question",
                                    value=Radio(
                                        answer=ClassificationAnswer(
                                            name="first_sub_radio_answer",
                                            confidence=0.8,
                                            classifications=[
                                                ClassificationAnnotation(
                                                    name="nested answer",
                                                    value=Text(
                                                        answer="nested answer",
                                                        confidence=0.7,
                                                    ),
                                                )
                                            ],
                                        )
                                    ),
                                )
                            ],
                        )
                    ]
                ),
            )
        ],
    )

    serialized = NDJsonConverter.serialize([label])
    res = next(serialized)

    assert res["dataRow"]["id"] == "bkj7z2q0b0000jx6x0q2q7q0d"
    answer = res["answer"][0]
    assert answer["confidence"] == 0.9
    assert answer["name"] == "first_answer"
    classification = answer["classifications"][0]
    nested_classification_answer = classification["answer"]
    assert nested_classification_answer["confidence"] == 0.8
    assert nested_classification_answer["name"] == "first_sub_radio_answer"
    sub_classification = nested_classification_answer["classifications"][0]
    assert sub_classification["name"] == "nested answer"
    assert sub_classification["answer"] == "nested answer"
    assert sub_classification["confidence"] == 0.7
