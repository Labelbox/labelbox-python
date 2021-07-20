import pytest
from labelbox.data.annotation_types.annotation import ClassificationAnnotation
from labelbox.data.annotation_types.classification import (CheckList,
                                                           ClassificationAnswer,
                                                           Dropdown, Radio,
                                                           Text)
from pydantic import ValidationError


def test_classification_answer():
    with pytest.raises(ValidationError):
        ClassificationAnswer()

    schema_id = "schema_id"
    display_name = "my_feature"
    answer = ClassificationAnswer(display_name=display_name)

    assert answer.schema_id is None
    assert answer.display_name == display_name

    answer = ClassificationAnswer(schema_id=schema_id,
                                  display_name=display_name)

    assert answer.schema_id == schema_id
    assert answer.display_name == display_name


def test_classification():
    answer = "1234"
    classification = ClassificationAnnotation(value=Text(answer=answer),
                                              display_name="a classification")
    assert classification.dict()['value']['answer'] == answer

    with pytest.raises(ValidationError):
        ClassificationAnnotation()


def test_subclass():
    answer = "1234"
    schema_id = "11232"
    display_name = "my_feature"
    with pytest.raises(ValidationError):
        # Should have feature schema info
        classification = ClassificationAnnotation(value=Text(answer=answer))
    classification = ClassificationAnnotation(value=Text(answer=answer),
                                              display_name=display_name)
    assert classification.dict() == {
        'display_name': display_name,
        'schema_id': None,
        'extra': {},
        'value': {
            'answer': answer
        },
        'classifications': []
    }
    classification = ClassificationAnnotation(value=Text(answer=answer),
                                              display_name=display_name,
                                              schema_id=schema_id)
    assert classification.dict() == {
        'display_name': None,
        'schema_id': schema_id,
        'extra': {},
        'value': {
            'answer': answer
        },
        'classifications': [],
        'display_name': display_name
    }
    classification = ClassificationAnnotation(value=Text(answer=answer),
                                              schema_id=schema_id,
                                              display_name=display_name)
    assert classification.dict() == {
        'display_name': display_name,
        'schema_id': schema_id,
        'extra': {},
        'value': {
            'answer': answer
        },
        'classifications': []
    }

    classification = ClassificationAnnotation(value=Text(answer=answer),
                                              display_name=display_name,
                                              schema_id=schema_id,
                                              classifications=[
                                                  ClassificationAnnotation(
                                                      value=Text(answer=answer),
                                                      display_name=display_name)
                                              ])

    assert classification.dict() == {
        'display_name':
            display_name,
        'extra': {},
        'schema_id':
            schema_id,
        'value': {
            'answer': answer
        },
        'classifications': [{
            'display_name': display_name,
            'extra': {},
            'schema_id': None,
            'value': {
                'answer': answer
            },
            'classifications': []
        }]
    }


def test_radio():
    answer = ClassificationAnswer(display_name="1")
    schema_id = "feature_schema_id"
    display_name = "my_feature"

    with pytest.raises(ValidationError):
        classification = ClassificationAnnotation(value=Radio(
            answer=answer.display_name))

    with pytest.raises(ValidationError):
        classification = Radio(answer=[answer])
    classification = Radio(answer=answer)
    assert classification.dict() == {
        'answer': {
            'display_name': answer.display_name,
            'schema_id': None,
            'extra': {}
        }
    }
    classification = ClassificationAnnotation(
        value=Radio(answer=answer),
        schema_id=schema_id,
        display_name=display_name,
        classifications=[
            ClassificationAnnotation(value=Radio(answer=answer),
                                     display_name=display_name)
        ])
    assert classification.dict() == {
        'display_name':
            display_name,
        'schema_id':
            schema_id,
        'extra': {},
        'value': {
            'answer': {
                'display_name': answer.display_name,
                'schema_id': None,
                'extra': {}
            }
        },
        'classifications': [{
            'display_name': display_name,
            'schema_id': None,
            'extra': {},
            'value': {
                'answer': {
                    'display_name': answer.display_name,
                    'schema_id': None,
                    'extra': {}
                }
            },
            'classifications': []
        }]
    }


def test_checklist():
    answer = ClassificationAnswer(display_name="1")
    schema_id = "feature_schema_id"
    display_name = "my_feature"

    with pytest.raises(ValidationError):
        classification = CheckList(answer=answer.display_name)

    with pytest.raises(ValidationError):
        classification = CheckList(answer=answer)

    classification = CheckList(answer=[answer])
    assert classification.dict() == {
        'answer': [{
            'display_name': answer.display_name,
            'schema_id': None,
            'extra': {}
        }]
    }
    classification = ClassificationAnnotation(
        value=CheckList(answer=[answer]),
        schema_id=schema_id,
        display_name=display_name,
        classifications=[
            ClassificationAnnotation(value=CheckList(answer=[answer]),
                                     display_name=display_name)
        ])
    assert classification.dict() == {
        'display_name':
            display_name,
        'schema_id':
            schema_id,
        'extra': {},
        'value': {
            'answer': [{
                'display_name': answer.display_name,
                'schema_id': None,
                'extra': {}
            }]
        },
        'classifications': [{
            'display_name': display_name,
            'schema_id': None,
            'extra': {},
            'value': {
                'answer': [{
                    'display_name': answer.display_name,
                    'schema_id': None,
                    'extra': {}
                }]
            },
            'classifications': []
        }]
    }


def test_dropdown():
    answer = ClassificationAnswer(display_name="1")
    schema_id = "feature_schema_id"
    display_name = "my_feature"

    with pytest.raises(ValidationError):
        classification = ClassificationAnnotation(
            value=Dropdown(answer=answer.display_name), display_name="test")

    with pytest.raises(ValidationError):
        classification = Dropdown(answer=answer)
    classification = Dropdown(answer=[answer])
    assert classification.dict() == {
        'answer': [{
            'display_name': '1',
            'schema_id': None,
            'extra': {}
        }]
    }
    classification = ClassificationAnnotation(
        value=Dropdown(answer=[answer]),
        schema_id=schema_id,
        display_name=display_name,
        classifications=[
            ClassificationAnnotation(value=Dropdown(answer=[answer]),
                                     display_name=display_name)
        ])
    assert classification.dict() == {
        'display_name':
            display_name,
        'schema_id':
            schema_id,
        'extra': {},
        'value': {
            'answer': [{
                'display_name': answer.display_name,
                'schema_id': None,
                'extra': {}
            }]
        },
        'classifications': [{
            'display_name': display_name,
            'schema_id': None,
            'extra': {},
            'value': {
                'answer': [{
                    'display_name': answer.display_name,
                    'schema_id': None,
                    'extra': {}
                }]
            },
            'classifications': []
        }]
    }
