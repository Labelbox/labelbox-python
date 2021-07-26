import pytest
from pydantic import ValidationError

from labelbox.data.annotation_types import (Text, Point, Line,
                                            ClassificationAnnotation,
                                            ObjectAnnotation,
                                            VideoClassificationAnnotation,
                                            VideoObjectAnnotation, TextEntity)


def test_annotation():
    name = "line_feature"
    line = Line(points=[Point(x=1, y=2), Point(x=2, y=2)])
    classification = Text(answer="1234")

    annotation = ObjectAnnotation(
        value=line,
        name=name,
    )
    assert annotation.value.points[0].dict() == {'extra': {}, 'x': 1., 'y': 2.}
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
