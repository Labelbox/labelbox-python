import pytest
from pydantic import ValidationError

from labelbox.data.annotation_types.geometry import Point, Line
from labelbox.data.annotation_types.classification.classification import Classification, Subclass, Text
from labelbox.data.annotation_types.annotation import Annotation, Frames, VideoAnnotation
from labelbox.data.annotation_types.ner import TextEntity


def test_annotation():
    display_name = "line_feature"
    line = Line(points=[Point(x=1, y=2), Point(x=2, y=2)])
    classification = Classification(value=Text(answer="1234"))

    annotation = Annotation(
        value=line,
        display_name=display_name,
    )
    assert annotation.value.points[0].dict() == {'x': 1., 'y': 2.}
    assert annotation.display_name == display_name

    # Check ner
    Annotation(
        value=TextEntity(start=10, end=12),
        display_name=display_name,
    )

    # Check classification
    Annotation(
        value=classification,
        display_name=display_name,
    )

    # Invalid subclass
    with pytest.raises(ValidationError):
        Annotation(
            value=line,
            display_name=display_name,
            classifications=[line],
        )

    # Classifications need to be a subclass, not a classification
    with pytest.raises(ValidationError):
        Annotation(
            value=line,
            display_name=display_name,
            classifications=[classification],
        )
    subclass = Subclass(**classification.dict(), display_name=display_name)

    Annotation(
        value=line,
        display_name=display_name,
        classifications=[subclass],
    )


def test_video_annotations():
    display_name = "line_feature"
    line = Line(points=[Point(x=1, y=2), Point(x=2, y=2)])
    # Missing frames
    with pytest.raises(ValidationError):
        VideoAnnotation(value=line, display_name=display_name)

    with pytest.raises(ValidationError):
        Frames(start=5, end=4)

    with pytest.raises(ValidationError):
        Frames(start=-1, end=4)

    VideoAnnotation(value=line,
                    display_name=display_name,
                    frames=[Frames(start=5, end=12)])
