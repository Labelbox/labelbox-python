from lbox.classification.checklist import Checklist
from lbox.classification.classification_annotation import ClassificationAnnotation
from lbox.classification.classification_answer import ClassificationAnswer
from lbox.data_row import DataRow
from lbox.label import Label


def test_serialization_min():
    label = Label(
        id="ckj7z2q0b0000jx6x0q2q7q0d",
        data_row=DataRow(
            id="bkj7z2q0b0000jx6x0q2q7q0d",
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

    res = label.model_dump(exclude_none=True, exclude=["extra"])
    annotation = res["annotations"][0]
    expected = {
        "name": "checkbox_question_geo",
        "data_row": {"id": "bkj7z2q0b0000jx6x0q2q7q0d"},
        "answer": [{"name": "first_answer"}],
    }
    assert annotation == expected
