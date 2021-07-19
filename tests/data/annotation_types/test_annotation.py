from labelbox.data.annotation_types.annotation import ClassificationAnnotation, ObjectAnnotation, VideoClassificationAnnotation, VideoObjectAnnotation
import pytest
from pydantic import ValidationError

from labelbox.data.annotation_types.geometry import Point, Line
from labelbox.data.annotation_types.classification.classification import Text
from labelbox.data.annotation_types.ner import TextEntity


def test_annotation():
    display_name = "line_feature"
    line = Line(points=[Point(x=1, y=2), Point(x=2, y=2)])
    classification = Text(answer="1234")

    annotation = ObjectAnnotation(
        value=line,
        display_name=display_name,
    )
    assert annotation.value.points[0].dict() == {'extra': {}, 'x': 1., 'y': 2.}
    assert annotation.display_name == display_name

    # Check ner
    ObjectAnnotation(
        value=TextEntity(start=10, end=12),
        display_name=display_name,
    )

    # Check classification
    ClassificationAnnotation(
        value=classification,
        display_name=display_name,
    )

    # Invalid subclass
    with pytest.raises(ValidationError):
        ObjectAnnotation(
            value=line,
            display_name=display_name,
            classifications=[line],
        )

    subclass = ClassificationAnnotation(value=classification,
                                        display_name=display_name)

    ObjectAnnotation(
        value=line,
        display_name=display_name,
        classifications=[subclass],
    )


def test_video_annotations():
    display_name = "line_feature"
    line = Line(points=[Point(x=1, y=2), Point(x=2, y=2)])

    # Wrong type
    with pytest.raises(ValidationError):
        VideoClassificationAnnotation(value=line,
                                      display_name=display_name,
                                      frame=1)

    # Missing frames
    with pytest.raises(ValidationError):
        VideoClassificationAnnotation(value=line, display_name=display_name)

    VideoObjectAnnotation(value=line,
                          display_name=display_name,
                          keyframe=True,
                          frame=2)
