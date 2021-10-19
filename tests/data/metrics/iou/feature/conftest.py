from types import SimpleNamespace

import pytest

from labelbox.data.annotation_types import ClassificationAnnotation, ObjectAnnotation
from labelbox.data.annotation_types import Polygon, Point


class NameSpace(SimpleNamespace):

    def __init__(self, predictions, ground_truths, expected):
        super(NameSpace, self).__init__(predictions=predictions,
                                        ground_truths=ground_truths,
                                        expected=expected)


@pytest.fixture
def different_classes():
    return [
        NameSpace(predictions=[
            ObjectAnnotation(name="cat",
                             value=Polygon(points=[
                                 Point(x=0, y=0),
                                 Point(x=10, y=0),
                                 Point(x=10, y=10),
                                 Point(x=0, y=10)
                             ]))
        ],
                  ground_truths=[
                      ObjectAnnotation(name="dog",
                                       value=Polygon(points=[
                                           Point(x=0, y=0),
                                           Point(x=10, y=0),
                                           Point(x=10, y=10),
                                           Point(x=0, y=10)
                                       ]))
                  ],
                  expected={
                      'cat': 0,
                      'dog': 0
                  })
    ]


@pytest.fixture
def one_overlap_class():
    return [
        NameSpace(predictions=[
            ObjectAnnotation(name="cat",
                             value=Polygon(points=[
                                 Point(x=0, y=0),
                                 Point(x=10, y=0),
                                 Point(x=10, y=10),
                                 Point(x=0, y=10)
                             ])),
            ObjectAnnotation(name="dog",
                             value=Polygon(points=[
                                 Point(x=0, y=0),
                                 Point(x=5, y=0),
                                 Point(x=5, y=5),
                                 Point(x=0, y=5)
                             ]))
        ],
                  ground_truths=[
                      ObjectAnnotation(name="dog",
                                       value=Polygon(points=[
                                           Point(x=0, y=0),
                                           Point(x=10, y=0),
                                           Point(x=10, y=10),
                                           Point(x=0, y=10)
                                       ]))
                  ],
                  expected={
                      'dog': 0.25,
                      'cat': 0.
                  }),
        NameSpace(predictions=[
            ObjectAnnotation(name="dog",
                             value=Polygon(points=[
                                 Point(x=0, y=0),
                                 Point(x=5, y=0),
                                 Point(x=5, y=5),
                                 Point(x=0, y=5)
                             ]))
        ],
                  ground_truths=[
                      ObjectAnnotation(name="dog",
                                       value=Polygon(points=[
                                           Point(x=0, y=0),
                                           Point(x=10, y=0),
                                           Point(x=10, y=10),
                                           Point(x=0, y=10)
                                       ])),
                      ObjectAnnotation(name="cat",
                                       value=Polygon(points=[
                                           Point(x=0, y=0),
                                           Point(x=10, y=0),
                                           Point(x=10, y=10),
                                           Point(x=0, y=10)
                                       ]))
                  ],
                  expected={
                      'dog': 0.25,
                      'cat': 0.
                  })
    ]


@pytest.fixture
def empty_annotations():
    return [
        NameSpace(predictions=[], ground_truths=[], expected={}),
        NameSpace(predictions=[],
                  ground_truths=[
                      ObjectAnnotation(name="dog",
                                       value=Polygon(points=[
                                           Point(x=0, y=0),
                                           Point(x=10, y=0),
                                           Point(x=10, y=10),
                                           Point(x=0, y=10)
                                       ])),
                      ObjectAnnotation(name="cat",
                                       value=Polygon(points=[
                                           Point(x=0, y=0),
                                           Point(x=10, y=0),
                                           Point(x=10, y=10),
                                           Point(x=0, y=10)
                                       ]))
                  ],
                  expected={
                      'dog': 0.,
                      'cat': 0.
                  }),
        NameSpace(predictions=[
            ObjectAnnotation(name="dog",
                             value=Polygon(points=[
                                 Point(x=0, y=0),
                                 Point(x=10, y=0),
                                 Point(x=10, y=10),
                                 Point(x=0, y=10)
                             ])),
            ObjectAnnotation(name="cat",
                             value=Polygon(points=[
                                 Point(x=0, y=0),
                                 Point(x=10, y=0),
                                 Point(x=10, y=10),
                                 Point(x=0, y=10)
                             ]))
        ],
                  ground_truths=[],
                  expected={
                      'dog': 0.,
                      'cat': 0.
                  })
    ]
