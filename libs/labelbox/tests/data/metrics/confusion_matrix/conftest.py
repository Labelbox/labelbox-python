from types import SimpleNamespace

import pytest

from labelbox.data.annotation_types import (
    ClassificationAnnotation,
    ObjectAnnotation,
)
from labelbox.data.annotation_types import (
    Polygon,
    Point,
    Rectangle,
    Mask,
    MaskData,
    Line,
    Radio,
    Text,
    Checklist,
    ClassificationAnswer,
)
import numpy as np

from labelbox.data.annotation_types.ner import TextEntity


class NameSpace(SimpleNamespace):
    def __init__(
        self,
        predictions,
        ground_truths,
        expected,
        expected_without_subclasses=None,
    ):
        super(NameSpace, self).__init__(
            predictions=predictions,
            ground_truths=ground_truths,
            expected=expected,
            expected_without_subclasses=expected_without_subclasses or expected,
        )


def get_radio(name, answer_name):
    return ClassificationAnnotation(
        name=name, value=Radio(answer=ClassificationAnswer(name=answer_name))
    )


def get_text(name, text_content):
    return ClassificationAnnotation(name=name, value=Text(answer=text_content))


def get_checklist(name, answer_names):
    return ClassificationAnnotation(
        name=name,
        value=Radio(
            answer=[
                ClassificationAnswer(name=answer_name)
                for answer_name in answer_names
            ]
        ),
    )


def get_polygon(name, points, subclasses=None):
    return ObjectAnnotation(
        name=name,
        value=Polygon(points=[Point(x=x, y=y) for x, y in points]),
        classifications=[] if subclasses is None else subclasses,
    )


def get_rectangle(name, start, end, subclasses=None):
    return ObjectAnnotation(
        name=name,
        value=Rectangle(
            start=Point(x=start[0], y=start[1]), end=Point(x=end[0], y=end[1])
        ),
        classifications=[] if subclasses is None else subclasses,
    )


def get_mask(name, pixels, color=(1, 1, 1), subclasses=None):
    mask = np.zeros((32, 32, 3)).astype(np.uint8)
    for pixel in pixels:
        mask[pixel[0], pixel[1]] = color
    return ObjectAnnotation(
        name=name,
        value=Mask(mask=MaskData(arr=mask), color=color),
        classifications=[] if subclasses is None else subclasses,
    )


def get_line(name, points, subclasses=None):
    return ObjectAnnotation(
        name=name,
        value=Line(points=[Point(x=x, y=y) for x, y in points]),
        classifications=[] if subclasses is None else subclasses,
    )


def get_point(name, x, y, subclasses=None):
    return ObjectAnnotation(
        name=name,
        value=Point(x=x, y=y),
        classifications=[] if subclasses is None else subclasses,
    )


def get_radio(name, answer_name):
    return ClassificationAnnotation(
        name=name, value=Radio(answer=ClassificationAnswer(name=answer_name))
    )


def get_checklist(name, answer_names):
    return ClassificationAnnotation(
        name=name,
        value=Checklist(
            answer=[
                ClassificationAnswer(name=answer_name)
                for answer_name in answer_names
            ]
        ),
    )


def get_ner(name, start, end, subclasses=None):
    return ObjectAnnotation(
        name=name,
        value=TextEntity(start=start, end=end),
        classifications=[] if subclasses is None else subclasses,
    )


def get_object_pairs(tool_fn, **kwargs):
    return [
        NameSpace(
            predictions=[tool_fn("cat", **kwargs)],
            ground_truths=[tool_fn("cat", **kwargs)],
            expected={"cat": [1, 0, 0, 0]},
        ),
        NameSpace(
            predictions=[
                tool_fn(
                    "cat",
                    **kwargs,
                    subclasses=[get_radio("is_animal", answer_name="yes")],
                )
            ],
            ground_truths=[
                tool_fn(
                    "cat",
                    **kwargs,
                    subclasses=[get_radio("is_animal", answer_name="yes")],
                )
            ],
            expected={"cat": [1, 0, 0, 0]},
            expected_without_subclasses={"cat": [1, 0, 0, 0]},
        ),
        NameSpace(
            predictions=[
                tool_fn(
                    "cat",
                    **kwargs,
                    subclasses=[get_radio("is_animal", answer_name="yes")],
                )
            ],
            ground_truths=[
                tool_fn(
                    "cat",
                    **kwargs,
                    subclasses=[get_radio("is_animal", answer_name="no")],
                )
            ],
            expected={"cat": [0, 1, 0, 1]},
            expected_without_subclasses={"cat": [1, 0, 0, 0]},
        ),
        NameSpace(
            predictions=[
                tool_fn(
                    "cat",
                    **kwargs,
                    subclasses=[get_radio("is_animal", answer_name="yes")],
                ),
                tool_fn(
                    "cat",
                    **kwargs,
                    subclasses=[get_radio("is_animal", answer_name="no")],
                ),
            ],
            ground_truths=[
                tool_fn(
                    "cat",
                    **kwargs,
                    subclasses=[get_radio("is_animal", answer_name="no")],
                )
            ],
            expected={"cat": [1, 1, 0, 0]},
            expected_without_subclasses={"cat": [1, 1, 0, 0]},
        ),
        NameSpace(
            predictions=[
                tool_fn(
                    "cat",
                    **kwargs,
                    subclasses=[get_radio("is_animal", answer_name="yes")],
                ),
                tool_fn(
                    "dog",
                    **kwargs,
                    subclasses=[get_radio("is_animal", answer_name="no")],
                ),
            ],
            ground_truths=[
                tool_fn(
                    "cat",
                    **kwargs,
                    subclasses=[get_radio("is_animal", answer_name="no")],
                )
            ],
            expected={"cat": [0, 1, 0, 1], "dog": [0, 1, 0, 0]},
            expected_without_subclasses={
                "cat": [1, 0, 0, 0],
                "dog": [0, 1, 0, 0],
            },
        ),
        NameSpace(
            predictions=[tool_fn("cat", **kwargs), tool_fn("cat", **kwargs)],
            ground_truths=[tool_fn("cat", **kwargs), tool_fn("cat", **kwargs)],
            expected={"cat": [2, 0, 0, 0]},
        ),
        NameSpace(
            predictions=[tool_fn("cat", **kwargs), tool_fn("cat", **kwargs)],
            ground_truths=[tool_fn("cat", **kwargs)],
            expected={"cat": [1, 1, 0, 0]},
        ),
        NameSpace(
            predictions=[tool_fn("cat", **kwargs)],
            ground_truths=[tool_fn("cat", **kwargs), tool_fn("cat", **kwargs)],
            expected={"cat": [1, 0, 0, 1]},
        ),
        NameSpace(
            predictions=[],
            ground_truths=[],
            expected=[],
            expected_without_subclasses=[],
        ),
        NameSpace(
            predictions=[],
            ground_truths=[tool_fn("cat", **kwargs)],
            expected={"cat": [0, 0, 0, 1]},
        ),
        NameSpace(
            predictions=[tool_fn("cat", **kwargs)],
            ground_truths=[],
            expected={"cat": [0, 1, 0, 0]},
        ),
        NameSpace(
            predictions=[tool_fn("cat", **kwargs)],
            ground_truths=[tool_fn("dog", **kwargs)],
            expected={"cat": [0, 1, 0, 0], "dog": [0, 0, 0, 1]},
        ),
    ]


@pytest.fixture
def radio_pairs():
    return [
        NameSpace(
            predictions=[get_radio("is_animal", answer_name="yes")],
            ground_truths=[get_radio("is_animal", answer_name="yes")],
            expected={"yes": [1, 0, 0, 0]},
        ),
        NameSpace(
            predictions=[get_radio("is_animal", answer_name="yes")],
            ground_truths=[get_radio("is_animal", answer_name="no")],
            expected={"no": [0, 0, 0, 1], "yes": [0, 1, 0, 0]},
        ),
        NameSpace(
            predictions=[get_radio("is_animal", answer_name="yes")],
            ground_truths=[],
            expected={"yes": [0, 1, 0, 0]},
        ),
        NameSpace(
            predictions=[],
            ground_truths=[get_radio("is_animal", answer_name="yes")],
            expected={"yes": [0, 0, 0, 1]},
        ),
        NameSpace(
            predictions=[
                get_radio("is_animal", answer_name="yes"),
                get_radio("is_short", answer_name="no"),
            ],
            ground_truths=[get_radio("is_animal", answer_name="yes")],
            expected={"no": [0, 1, 0, 0], "yes": [1, 0, 0, 0]},
        ),
        # Not supported yet:
        # NameSpace(
        # predictions=[],
        # ground_truths=[],
        # expected = [0,0,1,0]
        # )
    ]


@pytest.fixture
def checklist_pairs():
    return [
        NameSpace(
            predictions=[
                get_checklist("animal_attributes", answer_names=["striped"])
            ],
            ground_truths=[
                get_checklist("animal_attributes", answer_names=["striped"])
            ],
            expected={"striped": [1, 0, 0, 0]},
        ),
        NameSpace(
            predictions=[
                get_checklist("animal_attributes", answer_names=["striped"])
            ],
            ground_truths=[],
            expected={"striped": [0, 1, 0, 0]},
        ),
        NameSpace(
            predictions=[],
            ground_truths=[
                get_checklist("animal_attributes", answer_names=["striped"])
            ],
            expected={"striped": [0, 0, 0, 1]},
        ),
        NameSpace(
            predictions=[
                get_checklist(
                    "animal_attributes", answer_names=["striped", "short"]
                )
            ],
            ground_truths=[
                get_checklist("animal_attributes", answer_names=["striped"])
            ],
            expected={"short": [0, 1, 0, 0], "striped": [1, 0, 0, 0]},
        ),
        NameSpace(
            predictions=[
                get_checklist("animal_attributes", answer_names=["striped"])
            ],
            ground_truths=[
                get_checklist(
                    "animal_attributes", answer_names=["striped", "short"]
                )
            ],
            expected={"short": [0, 0, 0, 1], "striped": [1, 0, 0, 0]},
        ),
        NameSpace(
            predictions=[
                get_checklist(
                    "animal_attributes",
                    answer_names=["striped", "short", "black"],
                )
            ],
            ground_truths=[
                get_checklist(
                    "animal_attributes", answer_names=["striped", "short"]
                )
            ],
            expected={
                "black": [0, 1, 0, 0],
                "short": [1, 0, 0, 0],
                "striped": [1, 0, 0, 0],
            },
        ),
        NameSpace(
            predictions=[
                get_checklist(
                    "animal_attributes",
                    answer_names=["striped", "short", "black"],
                ),
                get_checklist("animal_name", answer_names=["doggy", "pup"]),
            ],
            ground_truths=[
                get_checklist(
                    "animal_attributes", answer_names=["striped", "short"]
                ),
                get_checklist("animal_name", answer_names=["pup"]),
            ],
            expected={
                "black": [0, 1, 0, 0],
                "doggy": [0, 1, 0, 0],
                "pup": [1, 0, 0, 0],
                "short": [1, 0, 0, 0],
                "striped": [1, 0, 0, 0],
            },
        ),
        # Not supported yet:
        # NameSpace(
        # predictions=[],
        # ground_truths=[],
        # expected = [0,0,1,0]
        # )
    ]


@pytest.fixture
def polygon_pairs():
    return get_object_pairs(
        get_polygon, points=[[0, 0], [10, 0], [10, 10], [0, 10]]
    )


@pytest.fixture
def rectangle_pairs():
    return get_object_pairs(get_rectangle, start=[0, 0], end=[10, 10])


@pytest.fixture
def mask_pairs():
    return get_object_pairs(get_mask, pixels=[[0, 0]])


@pytest.fixture
def line_pairs():
    return get_object_pairs(
        get_line, points=[[0, 0], [10, 0], [10, 10], [0, 10]]
    )


@pytest.fixture
def point_pairs():
    return get_object_pairs(get_point, x=0, y=0)


@pytest.fixture
def ner_pairs():
    return get_object_pairs(get_ner, start=0, end=10)


@pytest.fixture()
def pair_iou_thresholds():
    return [
        NameSpace(
            predictions=[
                get_polygon("cat", points=[[0, 0], [10, 0], [10, 10], [0, 10]]),
            ],
            ground_truths=[
                get_polygon("cat", points=[[0, 0], [5, 0], [5, 5], [0, 5]]),
            ],
            expected={0.2: [1, 0, 0, 0], 0.3: [0, 1, 0, 1]},
        ),
        NameSpace(
            predictions=[get_rectangle("cat", start=[0, 0], end=[10, 10])],
            ground_truths=[get_rectangle("cat", start=[0, 0], end=[5, 5])],
            expected={0.2: [1, 0, 0, 0], 0.3: [0, 1, 0, 1]},
        ),
        NameSpace(
            predictions=[get_point("cat", x=0, y=0)],
            ground_truths=[get_point("cat", x=20, y=20)],
            expected={0.5: [1, 0, 0, 0], 0.65: [0, 1, 0, 1]},
        ),
        NameSpace(
            predictions=[
                get_line("cat", points=[[0, 0], [10, 0], [10, 10], [0, 10]])
            ],
            ground_truths=[
                get_line("cat", points=[[0, 0], [100, 0], [100, 100], [0, 100]])
            ],
            expected={0.3: [1, 0, 0, 0], 0.65: [0, 1, 0, 1]},
        ),
        NameSpace(
            predictions=[
                get_mask("cat", pixels=[[0, 0], [1, 1], [2, 2], [3, 3]])
            ],
            ground_truths=[get_mask("cat", pixels=[[0, 0], [1, 1]])],
            expected={0.4: [1, 0, 0, 0], 0.6: [0, 1, 0, 1]},
        ),
    ]
