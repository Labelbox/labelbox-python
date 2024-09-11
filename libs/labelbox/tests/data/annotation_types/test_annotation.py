import pytest

from labelbox.data.annotation_types import (
    Text,
    Point,
    Line,
    ClassificationAnnotation,
    ObjectAnnotation,
    TextEntity,
)
from labelbox.data.annotation_types.video import VideoObjectAnnotation
from labelbox.data.annotation_types.geometry.rectangle import Rectangle
from labelbox.data.annotation_types.video import VideoClassificationAnnotation
from labelbox.exceptions import ConfidenceNotSupportedException
from pydantic import ValidationError


def test_annotation():
    name = "line_feature"
    line = Line(points=[Point(x=1, y=2), Point(x=2, y=2)])
    classification = Text(answer="1234")

    annotation = ObjectAnnotation(
        value=line,
        name=name,
    )
    assert annotation.value.points[0].model_dump() == {
        "extra": {},
        "x": 1.0,
        "y": 2.0,
    }
    assert annotation.name == name

    # Check ner
    ObjectAnnotation(
        value=TextEntity(start=10, end=12),
        name=name,
    )

    # Check classification
    ClassificationAnnotation(
        value=classification,
        name=name,
    )

    # Invalid subclass
    with pytest.raises(ValidationError):
        ObjectAnnotation(
            value=line,
            name=name,
            classifications=[line],
        )

    subclass = ClassificationAnnotation(value=classification, name=name)

    ObjectAnnotation(
        value=line,
        name=name,
        classifications=[subclass],
    )


def test_video_annotations():
    name = "line_feature"
    line = Line(points=[Point(x=1, y=2), Point(x=2, y=2)])

    # Wrong type
    with pytest.raises(ValidationError):
        VideoClassificationAnnotation(value=line, name=name, frame=1)

    # Missing frames
    with pytest.raises(ValidationError):
        VideoClassificationAnnotation(value=line, name=name)

    VideoObjectAnnotation(value=line, name=name, keyframe=True, frame=2)


def test_confidence_for_video_is_not_supported():
    with pytest.raises(ConfidenceNotSupportedException):
        (
            VideoObjectAnnotation(
                name="bbox toy",
                feature_schema_id="ckz38ofop0mci0z9i9w3aa9o4",
                extra={
                    "value": "bbox_toy",
                    "instanceURI": None,
                    "color": "#1CE6FF",
                    "feature_id": "cl1z52xw700000fhcayaqy0ev",
                },
                value=Rectangle(
                    extra={},
                    start=Point(extra={}, x=70.0, y=26.5),
                    end=Point(extra={}, x=561.0, y=348.0),
                ),
                classifications=[],
                frame=24,
                keyframe=False,
                confidence=0.3434,
            ),
        )


def test_confidence_value_range_validation():
    name = "line_feature"
    line = Line(points=[Point(x=1, y=2), Point(x=2, y=2)])

    with pytest.raises(ValueError) as e:
        ObjectAnnotation(value=line, name=name, confidence=14)
