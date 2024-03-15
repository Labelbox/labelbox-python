from labelbox.data.annotation_types.classification.classification import Text


def test_text():
    text_entity = Text(answer="good job")
    assert text_entity.answer == "good job"


def test_text_confidence():
    text_entity = Text(answer="good job", confidence=0.5)
    assert text_entity.answer == "good job"
    assert text_entity.confidence == 0.5
