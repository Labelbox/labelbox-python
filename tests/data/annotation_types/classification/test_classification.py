import pytest
from pydantic import ValidationError

from labelbox.data.annotation_types import (Checklist, ClassificationAnswer,
                                            Dropdown, Radio, Text,
                                            ClassificationAnnotation)


def test_classification_answer():
    with pytest.raises(ValidationError):
        ClassificationAnswer()

    feature_schema_id = "schema_id"
    name = "my_feature"
    answer = ClassificationAnswer(name=name)

    assert answer.feature_schema_id is None
    assert answer.name == name

    answer = ClassificationAnswer(feature_schema_id=feature_schema_id,
                                  name=name)

    assert answer.feature_schema_id == feature_schema_id
    assert answer.name == name


def test_classification():
    answer = "1234"
    classification = ClassificationAnnotation(value=Text(answer=answer),
                                              name="a classification")
    assert classification.dict()['value']['answer'] == answer

    with pytest.raises(ValidationError):
        ClassificationAnnotation()


def test_subclass():
    answer = "1234"
    feature_schema_id = "11232"
    name = "my_feature"
    with pytest.raises(ValidationError):
        # Should have feature schema info
        classification = ClassificationAnnotation(value=Text(answer=answer))
    classification = ClassificationAnnotation(value=Text(answer=answer),
                                              name=name)
    assert classification.dict() == {
        'name': name,
        'feature_schema_id': None,
        'extra': {},
        'value': {
            'answer': answer
        }
    }
    classification = ClassificationAnnotation(
        value=Text(answer=answer),
        name=name,
        feature_schema_id=feature_schema_id)
    assert classification.dict() == {
        'name': None,
        'feature_schema_id': feature_schema_id,
        'extra': {},
        'value': {
            'answer': answer
        },
        'name': name
    }
    classification = ClassificationAnnotation(
        value=Text(answer=answer),
        feature_schema_id=feature_schema_id,
        name=name)
    assert classification.dict() == {
        'name': name,
        'feature_schema_id': feature_schema_id,
        'extra': {},
        'value': {
            'answer': answer
        }
    }


def test_radio():
    answer = ClassificationAnswer(name="1")
    feature_schema_id = "feature_schema_id"
    name = "my_feature"

    with pytest.raises(ValidationError):
        classification = ClassificationAnnotation(value=Radio(
            answer=answer.name))

    with pytest.raises(ValidationError):
        classification = Radio(answer=[answer])
    classification = Radio(answer=answer)
    assert classification.dict() == {
        'answer': {
            'name': answer.name,
            'feature_schema_id': None,
            'extra': {}
        }
    }
    classification = ClassificationAnnotation(
        value=Radio(answer=answer),
        feature_schema_id=feature_schema_id,
        name=name)
    assert classification.dict() == {
        'name': name,
        'feature_schema_id': feature_schema_id,
        'extra': {},
        'value': {
            'answer': {
                'name': answer.name,
                'feature_schema_id': None,
                'extra': {}
            }
        }
    }


def test_checklist():
    answer = ClassificationAnswer(name="1")
    feature_schema_id = "feature_schema_id"
    name = "my_feature"

    with pytest.raises(ValidationError):
        classification = Checklist(answer=answer.name)

    with pytest.raises(ValidationError):
        classification = Checklist(answer=answer)

    classification = Checklist(answer=[answer])
    assert classification.dict() == {
        'answer': [{
            'name': answer.name,
            'feature_schema_id': None,
            'extra': {}
        }]
    }
    classification = ClassificationAnnotation(
        value=Checklist(answer=[answer]),
        feature_schema_id=feature_schema_id,
        name=name,
    )
    assert classification.dict() == {
        'name': name,
        'feature_schema_id': feature_schema_id,
        'extra': {},
        'value': {
            'answer': [{
                'name': answer.name,
                'feature_schema_id': None,
                'extra': {}
            }]
        },
    }


def test_dropdown():
    answer = ClassificationAnswer(name="1")
    feature_schema_id = "feature_schema_id"
    name = "my_feature"

    with pytest.raises(ValidationError):
        classification = ClassificationAnnotation(
            value=Dropdown(answer=answer.name), name="test")

    with pytest.raises(ValidationError):
        classification = Dropdown(answer=answer)
    classification = Dropdown(answer=[answer])
    assert classification.dict() == {
        'answer': [{
            'name': '1',
            'feature_schema_id': None,
            'extra': {}
        }]
    }
    classification = ClassificationAnnotation(
        value=Dropdown(answer=[answer]),
        feature_schema_id=feature_schema_id,
        name=name)
    assert classification.dict() == {
        'name': name,
        'feature_schema_id': feature_schema_id,
        'extra': {},
        'value': {
            'answer': [{
                'name': answer.name,
                'feature_schema_id': None,
                'extra': {}
            }]
        }
    }
