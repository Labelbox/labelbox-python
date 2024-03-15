import pytest

from labelbox.data.annotation_types import (Checklist, ClassificationAnswer,
                                            Dropdown, Radio, Text,
                                            ClassificationAnnotation)

from labelbox import pydantic_compat


def test_classification_answer():
    with pytest.raises(pydantic_compat.ValidationError):
        ClassificationAnswer()

    feature_schema_id = "schema_id"
    name = "my_feature"
    confidence = 0.9
    custom_metrics = [{'name': 'metric1', 'value': 2}]
    answer = ClassificationAnswer(name=name,
                                  confidence=confidence,
                                  custom_metrics=custom_metrics)

    assert answer.feature_schema_id is None
    assert answer.name == name
    assert answer.confidence == confidence
    assert answer.custom_metrics == custom_metrics

    answer = ClassificationAnswer(feature_schema_id=feature_schema_id,
                                  name=name)

    assert answer.feature_schema_id == feature_schema_id
    assert answer.name == name


def test_classification():
    answer = "1234"
    classification = ClassificationAnnotation(value=Text(answer=answer),
                                              name="a classification")
    assert classification.dict()['value']['answer'] == answer

    with pytest.raises(pydantic_compat.ValidationError):
        ClassificationAnnotation()


def test_subclass():
    answer = "1234"
    feature_schema_id = "11232"
    name = "my_feature"
    with pytest.raises(pydantic_compat.ValidationError):
        # Should have feature schema info
        classification = ClassificationAnnotation(value=Text(answer=answer))
    classification = ClassificationAnnotation(value=Text(answer=answer),
                                              name=name)
    assert classification.dict() == {
        'name': name,
        'feature_schema_id': None,
        'extra': {},
        'value': {
            'answer': answer,
        },
        'message_id': None,
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
            'answer': answer,
        },
        'name': name,
        'message_id': None,
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
            'answer': answer,
        },
        'message_id': None,
    }


def test_radio():
    answer = ClassificationAnswer(name="1",
                                  confidence=0.81,
                                  custom_metrics=[{
                                      'name': 'metric1',
                                      'value': 0.99
                                  }])
    feature_schema_id = "feature_schema_id"
    name = "my_feature"

    with pytest.raises(pydantic_compat.ValidationError):
        classification = ClassificationAnnotation(value=Radio(
            answer=answer.name))

    with pytest.raises(pydantic_compat.ValidationError):
        classification = Radio(answer=[answer])
    classification = Radio(answer=answer,)
    assert classification.dict() == {
        'answer': {
            'name': answer.name,
            'feature_schema_id': None,
            'extra': {},
            'confidence': 0.81,
            'custom_metrics': [{
                'name': 'metric1',
                'value': 0.99
            }],
        }
    }
    classification = ClassificationAnnotation(
        value=Radio(answer=answer),
        feature_schema_id=feature_schema_id,
        name=name,
        custom_metrics=[{
            'name': 'metric1',
            'value': 0.99
        }])
    assert classification.dict() == {
        'name': name,
        'feature_schema_id': feature_schema_id,
        'extra': {},
        'custom_metrics': [{
            'name': 'metric1',
            'value': 0.99
        }],
        'value': {
            'answer': {
                'name': answer.name,
                'feature_schema_id': None,
                'extra': {},
                'confidence': 0.81,
                'custom_metrics': [{
                    'name': 'metric1',
                    'value': 0.99
                }]
            },
        },
        'message_id': None,
    }


def test_checklist():
    answer = ClassificationAnswer(name="1",
                                  confidence=0.99,
                                  custom_metrics=[{
                                      'name': 'metric1',
                                      'value': 2
                                  }])
    feature_schema_id = "feature_schema_id"
    name = "my_feature"

    with pytest.raises(pydantic_compat.ValidationError):
        classification = Checklist(answer=answer.name)

    with pytest.raises(pydantic_compat.ValidationError):
        classification = Checklist(answer=answer)

    classification = Checklist(answer=[answer])
    assert classification.dict() == {
        'answer': [{
            'name': answer.name,
            'feature_schema_id': None,
            'extra': {},
            'confidence': 0.99,
            'custom_metrics': [{
                'name': 'metric1',
                'value': 2
            }],
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
                'extra': {},
                'confidence': 0.99,
                'custom_metrics': [{
                    'name': 'metric1',
                    'value': 2
                }],
            }]
        },
        'message_id': None,
    }


def test_dropdown():
    answer = ClassificationAnswer(name="1", confidence=1)
    feature_schema_id = "feature_schema_id"
    name = "my_feature"

    with pytest.raises(pydantic_compat.ValidationError):
        classification = ClassificationAnnotation(
            value=Dropdown(answer=answer.name), name="test")

    with pytest.raises(pydantic_compat.ValidationError):
        classification = Dropdown(answer=answer)
    classification = Dropdown(answer=[answer])
    assert classification.dict() == {
        'answer': [{
            'name': '1',
            'feature_schema_id': None,
            'extra': {},
            'confidence': 1
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
                'confidence': 1,
                'extra': {}
            }]
        },
        'message_id': None,
    }
