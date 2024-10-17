import numpy as np

import labelbox.types as lb_types
from labelbox.data.annotation_types import (
    PromptText,
    ObjectAnnotation,
    Point,
    Line,
    MaskData,
    Label,
)
import pytest


def test_schema_assignment_confidence():
    name = "line_feature"
    label = Label(
        data=MaskData(arr=np.ones((32, 32, 3), dtype=np.uint8), uid="test"),
        annotations=[
            ObjectAnnotation(
                value=Line(
                    points=[Point(x=1, y=2), Point(x=2, y=2)],
                ),
                name=name,
                confidence=0.914,
            )
        ],
    )

    assert label.annotations[0].confidence == 0.914


def test_initialize_label_no_coercion():
    global_key = "global-key"
    ner_annotation = lb_types.ObjectAnnotation(
        name="ner",
        value=lb_types.ConversationEntity(start=0, end=8, message_id="4"),
    )
    label = Label(
        data=lb_types.GenericDataRowData(global_key=global_key),
        annotations=[ner_annotation],
    )
    assert isinstance(label.data, lb_types.GenericDataRowData)
    assert label.data.global_key == global_key


def test_prompt_classification_validation():
    global_key = "global-key"
    prompt_text = lb_types.PromptClassificationAnnotation(
        name="prompt text", value=PromptText(answer="test")
    )
    prompt_text_2 = lb_types.PromptClassificationAnnotation(
        name="prompt text", value=PromptText(answer="test")
    )
    with pytest.raises(TypeError) as e_info:
        label = Label(
            data={"global_key": global_key},
            annotations=[prompt_text, prompt_text_2],
        )
