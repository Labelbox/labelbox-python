import pytest
from pydantic import ValidationError

from labelbox.data.annotation_types.classification import (
    CheckList,
    Classification,
    ClassificationAnswer,
    Dropdown,
    Radio,
    Text,
    Subclass
)


def test_classification_answer():
    with pytest.raises(ValidationError):
        ClassificationAnswer()

    schema_id = "schema_id"
    display_name = "my_feature"
    answer = ClassificationAnswer(schema_id=schema_id)

    assert answer.schema_id == schema_id
    assert answer.display_name is None

    answer = ClassificationAnswer(display_name=display_name)

    assert answer.schema_id is None
    assert answer.display_name == display_name

    answer = ClassificationAnswer(schema_id=schema_id,
                                  display_name=display_name)

    assert answer.schema_id == schema_id
    assert answer.display_name == display_name


def test_classification():
    answer = "1234"
    classification = Classification(value=Text(answer=answer))
    assert classification.dict()['value']['answer'] == answer

    with pytest.raises(ValidationError):
        Classification()


def test_subclass():
    answer = "1234"
    schema_id = "11232"
    display_name = "my_feature"
    with pytest.raises(ValidationError):
        # Should have feature schema info
        classification = Subclass(value=Text(answer=answer))
    classification = Subclass(value=Text(answer=answer),
                              display_name=display_name)
    assert classification.dict() == {
        'display_name': display_name,
        'schema_id': None,
        'value': {
            'answer': answer
        },
        'classifications': []
    }
    classification = Subclass(value=Text(answer=answer), schema_id=schema_id)
    assert classification.dict() == {
        'display_name': None,
        'schema_id': schema_id,
        'value': {
            'answer': answer
        },
        'classifications': []
    }
    classification = Subclass(value=Text(answer=answer),
                              schema_id=schema_id,
                              display_name=display_name)
    assert classification.dict() == {
        'display_name': display_name,
        'schema_id': schema_id,
        'value': {
            'answer': answer
        },
        'classifications': []
    }

    classification = Subclass(value=Text(answer=answer),
                              schema_id=schema_id,
                              classifications=[
                                  Subclass(value=Text(answer=answer),
                                           display_name=display_name)
                              ])
    assert classification.dict() == {
        'display_name':
            None,
        'schema_id':
            schema_id,
        'value': {
            'answer': answer
        },
        'classifications': [{
            'display_name': display_name,
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
        classification = Classification(value=Radio(answer=answer.display_name))

    with pytest.raises(ValidationError):
        classification = Classification(value=[Radio(answer=answer)])
    classification = Classification(value=Radio(answer=answer))
    assert classification.dict() == {
        'value': {
            'answer': {
                'display_name': answer.display_name,
                'schema_id': None
            }
        }
    }
    classification = Subclass(value=Radio(answer=answer),
                              schema_id=schema_id,
                              classifications=[
                                  Subclass(value=Radio(answer=answer),
                                           display_name=display_name)
                              ])
    assert classification.dict() == {
        'display_name':
            None,
        'schema_id':
            schema_id,
        'value': {
            'answer': {
                'display_name': answer.display_name,
                'schema_id': None
            }
        },
        'classifications': [{
            'display_name': display_name,
            'schema_id': None,
            'value': {
                'answer': {
                    'display_name': answer.display_name,
                    'schema_id': None
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
        classification = Classification(value=CheckList(
            answer=answer.display_name))

    with pytest.raises(ValidationError):
        classification = Classification(value=CheckList(answer=answer))

    classification = Classification(value=CheckList(answer=[answer]))
    assert classification.dict() == {
        'value': {
            'answer': [{
                'display_name': answer.display_name,
                'schema_id': None
            }]
        }
    }
    classification = Subclass(value=CheckList(answer=[answer]),
                              schema_id=schema_id,
                              classifications=[
                                  Subclass(value=CheckList(answer=[answer]),
                                           display_name=display_name)
                              ])
    assert classification.dict() == {
        'display_name':
            None,
        'schema_id':
            schema_id,
        'value': {
            'answer': [{
                'display_name': answer.display_name,
                'schema_id': None
            }]
        },
        'classifications': [{
            'display_name': display_name,
            'schema_id': None,
            'value': {
                'answer': [{
                    'display_name': answer.display_name,
                    'schema_id': None
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
        classification = Classification(value=Dropdown(
            answer=answer.display_name))

    with pytest.raises(ValidationError):
        classification = Classification(value=Dropdown(answer=answer))
    classification = Classification(value=Dropdown(answer=[answer]))
    assert classification.dict() == {
        'value': {
            'answer': [{
                'display_name': '1',
                'schema_id': None
            }]
        }
    }
    classification = Subclass(value=Dropdown(answer=[answer]),
                              schema_id=schema_id,
                              classifications=[
                                  Subclass(value=Dropdown(answer=[answer]),
                                           display_name=display_name)
                              ])
    assert classification.dict() == {
        'display_name':
            None,
        'schema_id':
            schema_id,
        'value': {
            'answer': [{
                'display_name': answer.display_name,
                'schema_id': None
            }]
        },
        'classifications': [{
            'display_name': display_name,
            'schema_id': None,
            'value': {
                'answer': [{
                    'display_name': answer.display_name,
                    'schema_id': None
                }]
            },
            'classifications': []
        }]
    }
