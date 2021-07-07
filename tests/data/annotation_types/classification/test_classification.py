from labelbox.data.annotation_types.classification.classification import Classification, ClassificationAnswer, Text, Subclass
import pytest
from pydantic import ValidationError



def test_classification_answer():
    with pytest.raises(ValidationError):
        ClassificationAnswer()

    schema_id = "schema_id"
    display_name = "my_feature"
    answer = ClassificationAnswer(schema_id = schema_id)

    assert answer.schema_id == schema_id
    assert answer.display_name is None

    answer = ClassificationAnswer(display_name = display_name)

    assert answer.schema_id is None
    assert answer.display_name == display_name

    answer = ClassificationAnswer(schema_id = schema_id, display_name = display_name)

    assert answer.schema_id == schema_id
    assert answer.display_name == display_name


def test_classification():
    answer = "1234"
    classification = Classification(value = Text(answer = answer))
    assert classification.dict()['value']['answer'] == answer

    with pytest.raises(ValidationError):
        Classification()


def test_subclass():
    answer = "1234"
    schema_id = "11232"
    display_name = "my_feature"
    with pytest.raises(ValidationError):
        # Should have feature schema info
        classification = Subclass(value = Text(answer = answer))
    classification = Subclass(value = Text(answer = answer), display_name = display_name)
    classification = Subclass(value = Text(answer = answer), schema_id = schema_id)
    classification = Subclass(value = Text(answer = answer), schema_id = schema_id, display_name = display_name)

    classification = Classification(value = Text(answer = answer))
    assert classification.dict()['value']['answer'] == answer

