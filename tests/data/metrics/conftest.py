from io import BytesIO
from types import SimpleNamespace
import pytest
import numpy as np
from PIL import Image


class NameSpace(SimpleNamespace):
    def __init__(self, predictions, labels, expected):
        super(NameSpace, self).__init__(predictions =  predictions,
                       labels = { 'objects' : labels, 'classifications' : []},
                       expected = expected)

@pytest.fixture
def polygon_pair():
    return NameSpace(labels=[{
        'featureId':
            'asdasds',
        'schemaId':
            '1234',
        'polygon': [{
            'x': 0,
            'y': 0
        }, {
            'x': 1,
            'y': 0
        }, {
            'x': 1,
            'y': 1
        }, {
            'x': 0,
            'y': 1
        }]
    }],
                           predictions=[{
                               'uuid':
                                   '12345',
                               'schemaId':
                                   '1234',
                               'polygon': [{
                                   'x': 0,
                                   'y': 0
                               }, {
                                   'x': 1,
                                   'y': 0
                               }, {
                                   'x': 1,
                                   'y': 0.5
                               }, {
                                   'x': 0,
                                   'y': 0.5
                               }]
                           }], expected = 0.5)

@pytest.fixture
def box_pair():
    return NameSpace(labels=[{
        'featureId': 'asdasds',
        'schemaId': '1234',
        "bbox": {
            "top": 1099,
            "left": 2010,
            "height": 690,
            "width": 591
        }
    }],
                           predictions=[{
                               'uuid': '12345',
                               'schemaId': '1234',
                               "bbox": {
                                   "top": 1099,
                                   "left": 2010,
                                   "height": 690,
                                   "width": 591
                               }
                           }], expected = 1.0)


@pytest.fixture
def unmatched_prediction():
    return NameSpace(labels=[{
        'featureId':
            'asdasds',
        'schemaId':
            '1234',
        'polygon': [{
            'x': 0,
            'y': 0
        }, {
            'x': 1,
            'y': 0
        }, {
            'x': 1,
            'y': 1
        }, {
            'x': 0,
            'y': 1
        }]
    }],
                           predictions=[{
                               'uuid':
                                   '12345',
                               'schemaId':
                                   '1234',
                               'polygon': [{
                                   'x': 0,
                                   'y': 0
                               }, {
                                   'x': 1,
                                   'y': 0
                               }, {
                                   'x': 1,
                                   'y': 0.5
                               }, {
                                   'x': 0,
                                   'y': 0.5
                               }]
                           }, {
                               'uuid':
                                   '12346',
                               'schemaId':
                                   '1234',
                               'polygon': [{
                                   'x': 10,
                                   'y': 10
                               }, {
                                   'x': 11,
                                   'y': 10
                               }, {
                                   'x': 11,
                                   'y': 1.5
                               }, {
                                   'x': 10,
                                   'y': 1.5
                               }]
                           }], expected = 0.25)


@pytest.fixture
def unmatched_label():
    return NameSpace(labels=[{
        'featureId':
            'asdasds1',
        'schemaId':
            '1234',
        'polygon': [{
            'x': 0,
            'y': 0
        }, {
            'x': 1,
            'y': 0
        }, {
            'x': 1,
            'y': 1
        }, {
            'x': 0,
            'y': 1
        }]
    }, {
        'featureId':
            'asdasds2',
        'schemaId':
            '1234',
        'polygon': [{
            'x': 10,
            'y': 10
        }, {
            'x': 11,
            'y': 10
        }, {
            'x': 11,
            'y': 11
        }, {
            'x': 10,
            'y': 11
        }]
    }],
                           predictions=[{
                               'uuid':
                                   '12345',
                               'schemaId':
                                   '1234',
                               'polygon': [{
                                   'x': 0,
                                   'y': 0
                               }, {
                                   'x': 1,
                                   'y': 0
                               }, {
                                   'x': 1,
                                   'y': 0.5
                               }, {
                                   'x': 0,
                                   'y': 0.5
                               }]
                           }], expected = 0.25)


def create_mask_url(indices, h, w):
    mask = np.zeros((h, w, 3), dtype=np.uint8)
    for idx in indices:
        mask[idx] = 1
    return mask


@pytest.fixture
def mask_pair():
    #* Use your own signed urls so that you can resign the data
    #* This is just to make the demo work
    return NameSpace(
        labels=[{
            'featureId': 'asdasds1',
            'schemaId': '1234',
            'instanceURI': create_mask_url([(0, 0, 0), (0, 1, 0)], 32, 32)
        }],
        predictions=[{
            'uuid': '12345',
            'schemaId': '1234',
            'instanceURI': create_mask_url([(0, 0, 0)], 32, 32)
        }], expected = 0.5)


@pytest.fixture
def matching_radio():
    return NameSpace(
        labels=[{
            'featureId': 'asdasds1',
            'schemaId': '1234',
            'answer': {
                'schemaId' : '1234'
            }
        }],
        predictions=[{
            'uuid': '12345',
            'schemaId': '1234',
                        'answer': {
                'schemaId' : '1234'
            }
        }], expected = 1.)

@pytest.fixture
def empty_radio_label():
    return NameSpace(
        labels=[],
        predictions=[{
            'uuid': '12345',
            'schemaId': '1234',
                        'answer': {
                'schemaId' : '1234'
            }
        }], expected = 0)

@pytest.fixture
def empty_radio_prediction():
    return NameSpace(
        labels=[{
            'featureId': 'asdasds1',
            'schemaId': '1234',
                        'answer': {
                'schemaId' : '1234'
            }
        }],
        predictions=[], expected = 0)



@pytest.fixture
def matching_checklist():
    return NameSpace(
        labels=[{
            'featureId': 'asdasds1',
            'schemaId': '1234',
            'uuid': '12345',
            'schemaId': '1234',
                        'answers': [{
                  'schemaId' : '1234',

            }, {'schemaId' : '356'},  {'schemaId' : '357'}]
        }],
        predictions=[{
            'uuid': '12345',
            'schemaId': '1234',
                        'answers': [{
                  'schemaId' : '1234',

            }, {'schemaId' : '356'}, {'schemaId' : '357'}]
        }], expected = 1.)

@pytest.fixture
def partially_matching_checklist_1():
    return NameSpace(
        labels=[{
            'featureId': 'asdasds1',
            'schemaId': '1234',
            'uuid': '12345',
            'schemaId': '1234',
                        'answers': [{
                  'schemaId' : '1234',

            }, {'schemaId' : '356'},  {'schemaId' : '357'}, {'schemaId' : '358'}]
        }],
        predictions=[{
            'uuid': '12345',
            'schemaId': '1234',
                        'answers': [{
                  'schemaId' : '1234',

            }, {'schemaId' : '356'},  {'schemaId' : '357'}, {'schemaId' : '3589999'}]
        }], expected = 0.6)


@pytest.fixture
def partially_matching_checklist_2():
    return NameSpace(
        labels=[{
            'featureId': 'asdasds1',
            'schemaId': '1234',
            'uuid': '12345',
            'schemaId': '1234',
                        'answers': [{
                  'schemaId' : '1234',

            }, {'schemaId' : '356'}]
        }],
        predictions=[{
            'uuid': '12345',
            'schemaId': '1234',
                        'answers': [{
                  'schemaId' : '1234',

            }, {'schemaId' : '356'},  {'schemaId' : '357'}, {'schemaId' : '3589999'}]
        }], expected = 0.5)


@pytest.fixture
def partially_matching_checklist_3():
    return NameSpace(
        labels=[{
            'featureId': 'asdasds1',
            'schemaId': '1234',
            'uuid': '12345',
            'schemaId': '1234',
                                    'answers': [{
                  'schemaId' : '1234',

            }, {'schemaId' : '356'},  {'schemaId' : '357'}, {'schemaId' : '3589999'}]

        }],
        predictions=[{
            'uuid': '12345',
            'schemaId': '1234',
                        'answers': [{
                  'schemaId' : '1234',

            }, {'schemaId' : '356'}]
        }], expected = 0.5)

@pytest.fixture
def empty_checklist_label():
    return NameSpace(
        labels=[],
        predictions=[{
            'uuid': '12345',
            'schemaId': '1234',
                        'answers': [{
                'schemaId' : '1234'
            }]
        }], expected = 0)

@pytest.fixture
def empty_checklist_prediction():
    return NameSpace(
        labels=[{
            'featureId': 'asdasds1',
            'schemaId': '1234',
                        'answers': [{
                'schemaId' : '1234'
            }]
        }],
        predictions=[], expected = 0)


@pytest.fixture
def matching_text():
    return NameSpace(
        labels=[{
            'featureId': 'asdasds1',
            'schemaId': '1234',
                        'answer': 'test'
        }],
        predictions=[{
            'uuid': '12345',
            'schemaId': '1234',
        'answer': 'test'}], expected = 1.0)


@pytest.fixture
def not_matching_text():
    return NameSpace(
        labels=[{
            'featureId': 'asdasds1',
            'schemaId': '1234',
                        'answer': 'test'
        }],
        predictions=[{
            'uuid': '12345',
            'schemaId': '1234',
        'answer': 'not_test'}], expected = 0.)


@pytest.fixture
def test_box_with_subclass():
    return NameSpace(labels=[{
        'featureId': 'asdasds',
        'schemaId': '1234',
        "bbox": {
            "top": 1099,
            "left": 2010,
            "height": 690,
            "width": 591
        },
    'classifications' : [{
        'schemaId': '1234',
        'answer': 'test'
    }
    ]}],
                           predictions=[{
                               'uuid': '12345',
                               'schemaId': '1234',
                               "bbox": {
                                   "top": 1099,
                                   "left": 2010,
                                   "height": 690,
                                   "width": 591
                               },
                               'classifications' : [{
        'schemaId': '1234',
        'answer': 'test'
                               }
    ]
                           }], expected = 1.0)


@pytest.fixture
def test_box_with_wrong_subclass():
    return NameSpace(labels=[{
        'featureId': 'asdasds',
        'schemaId': '1234',
        "bbox": {
            "top": 1099,
            "left": 2010,
            "height": 690,
            "width": 591
        },
    'classifications' : [{
        'schemaId': '1234',
        'answer': 'test'
    }
    ]}],
                           predictions=[{
                               'uuid': '12345',
                               'schemaId': '1234',
                               "bbox": {
                                   "top": 1099,
                                   "left": 2010,
                                   "height": 690,
                                   "width": 591
                               },
                               'classifications' : [{
        'schemaId': '1234',
        'answer': 'not_test'
                               }
    ]
                           }], expected = 0.5)



@pytest.fixture
def line_pair():
    return NameSpace(labels=[{
        'featureId': 'asdasds',
        'schemaId': '1234',
        "line":
            [{ "x" :0, "y" : 100}, { "x" :0, "y" : 0}],
    }],
                           predictions=[{
                               'uuid': '12345',
                               'schemaId': '1234',
                                "line":
            [{ "x" :5, "y" : 95}, { "x" :0, "y" : 0}],
                           }], expected = 0.9496975567603978)


@pytest.fixture
def point_pair():
    return NameSpace(labels=[{
        'featureId': 'asdasds',
        'schemaId': '1234',
        "point": {'x' : 0, 'y' : 0}
    }],
                           predictions=[{
                               'uuid': '12345',
                               'schemaId': '1234',
                                "point": {'x' : 5, 'y' : 5}

                           }], expected = 0.879113232477017)
