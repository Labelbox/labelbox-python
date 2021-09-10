from types import SimpleNamespace

import pytest

from labelbox.data.annotation_types import ClassificationAnnotation, ObjectAnnotation
from labelbox.data.annotation_types import Polygon, Point, Rectangle, Mask, MaskData, Line, Radio, Text, Checklist, ClassificationAnswer
import numpy as np

class NameSpace(SimpleNamespace):

    def __init__(self, predictions, ground_truths, expected):
        super(NameSpace, self).__init__(predictions=predictions,
                                        ground_truths=ground_truths,
                                        expected=expected)


def get_radio(name, answer_name):
    return ClassificationAnnotation(
        name = name,
        value = Radio(answer = ClassificationAnswer(name = answer_name))
    )

def get_text(name, text_content):
    return ClassificationAnnotation(
        name = name,
        value = Text(answer = text_content)
    )

def get_checklist(name, answer_names):
    return ClassificationAnnotation(
        name = name,
        value = Radio(answer = [ClassificationAnswer(name = answer_name) for answer_name in answer_names])
    )


def get_polygon(name, points, subclasses = None):
    return ObjectAnnotation(name = name,
      value = Polygon( points = [Point(x = x, y = y) for x,y in points]),
      classifications = [] if subclasses is None else subclasses
    )

def get_rectangle(name, start, end):
    return ObjectAnnotation(name = name,
      value = Rectangle( start = Point(x = start[0], y = start[1]), end = Point(x = end[0], y = end[1]))
    )

def get_mask(name, pixels, color = (1,1,1)):
    mask = np.zeros((32,32,3)).astype(np.uint8)
    for pixel in pixels:
        mask[pixel[0], pixel[1]] = color
    return ObjectAnnotation(name=name,
                    value=Mask(mask = MaskData(arr = mask), color =color)
    )

def get_line(name, points):
    return ObjectAnnotation(name = name,
      value = Line( points = [Point(x = x, y = y) for x,y in points])
    )

def get_point(name, x, y):
    return ObjectAnnotation(name = name,
      value = Point(x = x, y = y)
    )


def get_object_pairs(tool_fn, **kwargs):
    return [
        NameSpace(
            predictions=[
                tool_fn("cat", **kwargs)
            ],
            ground_truths=[
                tool_fn("cat", **kwargs)
            ],
            expected = [1,0,0,0]
            ),
        NameSpace(
            predictions=[
                tool_fn("cat", **kwargs),
                tool_fn("cat", **kwargs)
            ],
            ground_truths=[
                tool_fn("cat", **kwargs),
                tool_fn("cat", **kwargs)
            ],
            expected = [2,0,0,0]
            ),
        NameSpace(
            predictions=[
                tool_fn("cat", **kwargs),
                tool_fn("cat", **kwargs)
            ],
            ground_truths=[
                tool_fn("cat", **kwargs)
            ],
            expected = [1,1,0,0]
            ),
        NameSpace(
            predictions=[
                tool_fn("cat", **kwargs)
            ],
            ground_truths=[
                tool_fn("cat", **kwargs),
                tool_fn("cat", **kwargs)
            ],
            expected = [1,0,0,1]
            ),
        NameSpace(
            predictions=[],
            ground_truths=[],
            expected = []
            ),
        NameSpace(
            predictions=[],
            ground_truths=[
                tool_fn("cat", **kwargs)
            ],
            expected = [0,0,0,1]
            ),
        NameSpace(
            predictions=[
                tool_fn("cat", **kwargs)
            ],
            ground_truths=[],
            expected = [0,1,0,0]
            ),
        NameSpace(
            predictions=[
                tool_fn("cat", **kwargs)
            ],
            ground_truths=[
                tool_fn("dog", **kwargs)
            ],
            expected = [0,1,0,1]
            ),
    ]

@pytest.fixture
def polygon_pair():
    return get_object_pairs(get_polygon, points = [[0,0], [10,0], [10,10], [0,10]] )


@pytest.fixture
def rectangle_pair():
    return get_object_pairs(get_rectangle, start = [0,0], end = [10,10] )

@pytest.fixture
def mask_pair():
    return get_object_pairs(get_mask, pixels = [[0,0]])

@pytest.fixture
def line_pair():
    return get_object_pairs(get_line, points = [[0,0], [10,0], [10,10], [0,10]])

@pytest.fixture
def point_pair():
    return get_object_pairs(get_point, x = 0, y = 0)


"""
def get_radio(name, answer_name):
    return ClassificationAnnotation(
        name = name,
        value = Radio(answer = ClassificationAnswer(name = answer_name))
    )

def get_text(name, text_content):
    return ClassificationAnnotation(
        name = name,
        value = Text(answer = text_content)
    )

def get_checklist(name, answer_names):
    return ClassificationAnnotation(
        name = name,
        value = Radio(answer = [ClassificationAnswer(name = answer_name) for answer_name in answer_names])
    )

@pytest.fixture
def radio_pairs():
    return [
        NameSpace(
            predictions=[get_radio("is_animal", answer_name = "yes")],
            ground_truths=[get_radio("is_animal", answer_name = "yes")],
            expected = [1,0,0,0]
            ),
        NameSpace(
            predictions=[get_radio("is_animal", answer_name = "yes")],
            ground_truths=[get_radio("is_animal", answer_name = "no")],
            expected = [1,0,0,0]
            ),
        NameSpace(
            predictions=[
                get_radio("is_animal", answer_name = "yes")
            ],
            ground_truths=[],
            expected = [0,1,0,0]
            ),
            NameSpace(
            predictions=[],
            ground_truths=[get_radio("is_animal", answer_name = "yes")],
            expected = [0,0,0,1]
            ),
            NameSpace(
            predictions=[],
            ground_truths=[],
            expected = [0,0,1,0]
            )
    ]


@pytest.fixture
def radio_pairs():
    return [
        NameSpace(
            predictions=[get_text("animal_name", answer_name = "yes")],
            ground_truths=[get_text("animal_name", answer_name = "yes")],
            expected = [1,0,0,0]
            ),
        NameSpace(
            predictions=[
                get_text("is_animal", answer_name = "yes")
            ],
            ground_truths=[],
            expected = [0,1,0,0]
            ),
            NameSpace(
            predictions=[],
            ground_truths=[get_text("is_animal", answer_name = "yes")],
            expected = [0,0,0,1]
            ),
            NameSpace(
            predictions=[],
            ground_truths=[],
            expected = [0,0,1,0]
            )
    ]

# TODO: Do we actually capture true negatives? We def should for classifications. and maybe for non-classifications too..
# TODO: Change the values to be named. I can't even keep track of this shit

"""

# Current question.. how do we handle classification precision and recall...

