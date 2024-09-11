import pytest

from labelbox.data.annotation_types import (
    Checklist,
    ClassificationAnswer,
    Radio,
    Text,
    ClassificationAnnotation,
)

from pydantic import ValidationError


def test_classification_answer():
    with pytest.raises(ValidationError):
        ClassificationAnswer()

    feature_schema_id = "immunoelectrophoretically"
    name = "my_feature"
    confidence = 0.9
    custom_metrics = [{"name": "metric1", "value": 2}]
    answer = ClassificationAnswer(
        name=name, confidence=confidence, custom_metrics=custom_metrics
    )

    assert answer.feature_schema_id is None
    assert answer.name == name
    assert answer.confidence == confidence
    assert [
        answer.custom_metrics[0].model_dump(exclude_none=True)
    ] == custom_metrics

    answer = ClassificationAnswer(
        feature_schema_id=feature_schema_id, name=name
    )

    assert answer.feature_schema_id == feature_schema_id
    assert answer.name == name


def test_classification():
    answer = "1234"
    classification = ClassificationAnnotation(
        value=Text(answer=answer), name="a classification"
    )
    assert (
        classification.model_dump(exclude_none=True)["value"]["answer"]
        == answer
    )

    with pytest.raises(ValidationError):
        ClassificationAnnotation()


def test_subclass():
    answer = "1234"
    feature_schema_id = "immunoelectrophoretically"
    name = "my_feature"
    with pytest.raises(ValidationError):
        # Should have feature schema info
        classification = ClassificationAnnotation(value=Text(answer=answer))
    classification = ClassificationAnnotation(
        value=Text(answer=answer), name=name
    )
    assert classification.model_dump(exclude_none=True) == {
        "name": name,
        "extra": {},
        "value": {
            "answer": answer,
        },
    }
    classification = ClassificationAnnotation(
        value=Text(answer=answer),
        name=name,
        feature_schema_id=feature_schema_id,
    )
    assert classification.model_dump(exclude_none=True) == {
        "feature_schema_id": feature_schema_id,
        "extra": {},
        "value": {
            "answer": answer,
        },
        "name": name,
    }
    classification = ClassificationAnnotation(
        value=Text(answer=answer),
        feature_schema_id=feature_schema_id,
        name=name,
    )
    assert classification.model_dump(exclude_none=True) == {
        "name": name,
        "feature_schema_id": feature_schema_id,
        "extra": {},
        "value": {
            "answer": answer,
        },
    }


def test_radio():
    answer = ClassificationAnswer(
        name="1",
        confidence=0.81,
        custom_metrics=[{"name": "metric1", "value": 0.99}],
    )
    feature_schema_id = "immunoelectrophoretically"
    name = "my_feature"

    with pytest.raises(ValidationError):
        classification = ClassificationAnnotation(
            value=Radio(answer=answer.name)
        )

    with pytest.raises(ValidationError):
        classification = Radio(answer=[answer])
    classification = Radio(answer=answer)

    assert classification.model_dump(exclude_none=True) == {
        "answer": {
            "name": answer.name,
            "extra": {},
            "confidence": 0.81,
            "custom_metrics": [{"name": "metric1", "value": 0.99}],
        }
    }
    classification = ClassificationAnnotation(
        value=Radio(answer=answer),
        feature_schema_id=feature_schema_id,
        name=name,
        custom_metrics=[{"name": "metric1", "value": 0.99}],
    )
    assert classification.model_dump(exclude_none=True) == {
        "name": name,
        "feature_schema_id": feature_schema_id,
        "extra": {},
        "custom_metrics": [{"name": "metric1", "value": 0.99}],
        "value": {
            "answer": {
                "name": answer.name,
                "extra": {},
                "confidence": 0.81,
                "custom_metrics": [{"name": "metric1", "value": 0.99}],
            },
        },
    }


def test_checklist():
    answer = ClassificationAnswer(
        name="1",
        confidence=0.99,
        custom_metrics=[{"name": "metric1", "value": 2}],
    )
    feature_schema_id = "immunoelectrophoretically"
    name = "my_feature"

    with pytest.raises(ValidationError):
        classification = Checklist(answer=answer.name)

    with pytest.raises(ValidationError):
        classification = Checklist(answer=answer)

    classification = Checklist(answer=[answer])
    assert classification.model_dump(exclude_none=True) == {
        "answer": [
            {
                "name": answer.name,
                "extra": {},
                "confidence": 0.99,
                "custom_metrics": [{"name": "metric1", "value": 2}],
            }
        ]
    }
    classification = ClassificationAnnotation(
        value=Checklist(answer=[answer]),
        feature_schema_id=feature_schema_id,
        name=name,
    )
    assert classification.model_dump(exclude_none=True) == {
        "name": name,
        "feature_schema_id": feature_schema_id,
        "extra": {},
        "value": {
            "answer": [
                {
                    "name": answer.name,
                    "extra": {},
                    "confidence": 0.99,
                    "custom_metrics": [{"name": "metric1", "value": 2}],
                }
            ]
        },
    }
