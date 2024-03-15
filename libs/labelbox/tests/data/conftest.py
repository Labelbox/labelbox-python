import pytest

from labelbox.data.annotation_types.classification.classification import Checklist, ClassificationAnnotation, ClassificationAnswer, Radio
from labelbox.data.annotation_types.geometry.point import Point
from labelbox.data.annotation_types.geometry.rectangle import Rectangle
from labelbox.data.annotation_types.video import VideoObjectAnnotation


@pytest.fixture
def bbox_video_annotation_objects():
    bbox_annotation = [
        VideoObjectAnnotation(
            name="bbox",
            keyframe=True,
            frame=13,
            segment_index=0,
            value=Rectangle(
                start=Point(x=146.0, y=98.0),  # Top left
                end=Point(x=382.0, y=341.0),  # Bottom right
            ),
            classifications=[
                ClassificationAnnotation(
                    name='nested',
                    value=Radio(answer=ClassificationAnswer(
                        name='radio_option_1',
                        classifications=[
                            ClassificationAnnotation(
                                name='nested_checkbox',
                                value=Checklist(answer=[
                                    ClassificationAnswer(
                                        name='nested_checkbox_option_1'),
                                    ClassificationAnswer(
                                        name='nested_checkbox_option_2')
                                ]))
                        ])),
                )
            ]),
        VideoObjectAnnotation(
            name="bbox",
            keyframe=True,
            frame=19,
            segment_index=0,
            value=Rectangle(
                start=Point(x=186.0, y=98.0),  # Top left
                end=Point(x=490.0, y=341.0),  # Bottom right
            ))
    ]

    return bbox_annotation
