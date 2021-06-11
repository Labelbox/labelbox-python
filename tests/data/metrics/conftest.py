from io import BytesIO
from types import SimpleNamespace
import pytest
import numpy as np
from PIL import Image


class NameSpace(SimpleNamespace):

    def __init__(self, predictions, labels, expected):
        super(NameSpace,
              self).__init__(predictions=predictions,
                             labels={
                                 'DataRow ID': 'ckppihxc10005aeyjen11h7jh',
                                 'Label': {
                                     'objects': labels,
                                     'classifications': []
                                 }
                             },
                             expected=expected)


@pytest.fixture
def polygon_pair():
    return NameSpace(labels=[{
        'featureId':
            'ckppivl7p0006aeyj92cezr9d',
        'schemaId':
            'ckppid25v0000aeyjmxfwlc7t',
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
                             '76e0dcea-fe46-43e5-95f5-a5e3f378520a',
                         'schemaId':
                             'ckppid25v0000aeyjmxfwlc7t',
                         'dataRow': {
                             'id': 'ckppihxc10005aeyjen11h7jh'
                         },
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
                     }],
                     expected=0.5)


@pytest.fixture
def box_pair():
    return NameSpace(labels=[{
        'featureId': 'ckppivl7p0006aeyj92cezr9d',
        'schemaId': 'ckppid25v0000aeyjmxfwlc7t',
        "bbox": {
            "top": 1099,
            "left": 2010,
            "height": 690,
            "width": 591
        }
    }],
                     predictions=[{
                         'uuid': '76e0dcea-fe46-43e5-95f5-a5e3f378520a',
                         'schemaId': 'ckppid25v0000aeyjmxfwlc7t',
                         'dataRow': {
                             'id': 'ckppihxc10005aeyjen11h7jh'
                         },
                         "bbox": {
                             "top": 1099,
                             "left": 2010,
                             "height": 690,
                             "width": 591
                         }
                     }],
                     expected=1.0)


@pytest.fixture
def unmatched_prediction():
    return NameSpace(labels=[{
        'featureId':
            'ckppivl7p0006aeyj92cezr9d',
        'schemaId':
            'ckppid25v0000aeyjmxfwlc7t',
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
                             '76e0dcea-fe46-43e5-95f5-a5e3f378520a',
                         'schemaId':
                             'ckppid25v0000aeyjmxfwlc7t',
                         'dataRow': {
                             'id': 'ckppihxc10005aeyjen11h7jh'
                         },
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
                             'd0ba2520-02e9-47d4-8736-088bbdbabbc3',
                         'schemaId':
                             'ckppid25v0000aeyjmxfwlc7t',
                         'dataRow': {
                             'id': 'ckppihxc10005aeyjen11h7jh'
                         },
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
                     }],
                     expected=0.25)


@pytest.fixture
def unmatched_label():
    return NameSpace(labels=[{
        'featureId':
            '1234567890111213141516171',
        'schemaId':
            'ckppid25v0000aeyjmxfwlc7t',
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
            'ckppiw3bs0007aeyjs3pvrqzi',
        'schemaId':
            'ckppid25v0000aeyjmxfwlc7t',
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
                             '76e0dcea-fe46-43e5-95f5-a5e3f378520a',
                         'schemaId':
                             'ckppid25v0000aeyjmxfwlc7t',
                         'dataRow': {
                             'id': 'ckppihxc10005aeyjen11h7jh'
                         },
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
                     }],
                     expected=0.25)


def create_mask_url(indices, h, w):
    mask = np.zeros((h, w, 3), dtype=np.uint8)
    for idx in indices:
        mask[idx] = 1
    return mask.tobytes()


@pytest.fixture
def mask_pair():
    #* Use your own signed urls so that you can resign the data
    #* This is just to make the demo work
    return NameSpace(labels=[{
        'featureId': '1234567890111213141516171',
        'schemaId': 'ckppid25v0000aeyjmxfwlc7t',
        'instanceURI': create_mask_url([(0, 0, 0), (0, 1, 0)], 32, 32)
    }],
                     predictions=[{
                         'uuid': '76e0dcea-fe46-43e5-95f5-a5e3f378520a',
                         'schemaId': 'ckppid25v0000aeyjmxfwlc7t',
                         'dataRow': {
                             'id': 'ckppihxc10005aeyjen11h7jh'
                         },
                         'mask': {
                             'instanceURI':
                                 create_mask_url([(0, 0, 0)], 32, 32),
                             'colorRGB': (1, 1, 1)
                         }
                     }],
                     expected=0.5)


@pytest.fixture
def matching_radio():
    return NameSpace(labels=[{
        'featureId': '1234567890111213141516171',
        'schemaId': 'ckppid25v0000aeyjmxfwlc7t',
        'answer': {
            'schemaId': 'ckppid25v0000aeyjmxfwlc7t'
        }
    }],
                     predictions=[{
                         'uuid': '76e0dcea-fe46-43e5-95f5-a5e3f378520a',
                         'schemaId': 'ckppid25v0000aeyjmxfwlc7t',
                         'dataRow': {
                             'id': 'ckppihxc10005aeyjen11h7jh'
                         },
                         'answer': {
                             'schemaId': 'ckppid25v0000aeyjmxfwlc7t'
                         }
                     }],
                     expected=1.)


@pytest.fixture
def empty_radio_label():
    return NameSpace(labels=[],
                     predictions=[{
                         'uuid': '76e0dcea-fe46-43e5-95f5-a5e3f378520a',
                         'schemaId': 'ckppid25v0000aeyjmxfwlc7t',
                         'dataRow': {
                             'id': 'ckppihxc10005aeyjen11h7jh'
                         },
                         'answer': {
                             'schemaId': 'ckppid25v0000aeyjmxfwlc7t'
                         }
                     }],
                     expected=0)


@pytest.fixture
def empty_radio_prediction():
    return NameSpace(labels=[{
        'featureId': '1234567890111213141516171',
        'schemaId': 'ckppid25v0000aeyjmxfwlc7t',
        'answer': {
            'schemaId': 'ckppid25v0000aeyjmxfwlc7t'
        }
    }],
                     predictions=[],
                     expected=0)


@pytest.fixture
def matching_checklist():
    return NameSpace(labels=[{
        'featureId':
            '1234567890111213141516171',
        'schemaId':
            'ckppid25v0000aeyjmxfwlc7t',
        'uuid':
            '76e0dcea-fe46-43e5-95f5-a5e3f378520a',
        'schemaId':
            'ckppid25v0000aeyjmxfwlc7t',
        'answers': [{
            'schemaId': 'ckppid25v0000aeyjmxfwlc7t',
        }, {
            'schemaId': 'ckppide010001aeyj0yhiaghc'
        }, {
            'schemaId': 'ckppidq4u0002aeyjmcc4toxw'
        }]
    }],
                     predictions=[{
                         'uuid':
                             '76e0dcea-fe46-43e5-95f5-a5e3f378520a',
                         'schemaId':
                             'ckppid25v0000aeyjmxfwlc7t',
                         'dataRow': {
                             'id': 'ckppihxc10005aeyjen11h7jh'
                         },
                         'answers': [{
                             'schemaId': 'ckppid25v0000aeyjmxfwlc7t',
                         }, {
                             'schemaId': 'ckppide010001aeyj0yhiaghc'
                         }, {
                             'schemaId': 'ckppidq4u0002aeyjmcc4toxw'
                         }]
                     }],
                     expected=1.)


@pytest.fixture
def partially_matching_checklist_1():
    return NameSpace(labels=[{
        'featureId':
            '1234567890111213141516171',
        'schemaId':
            'ckppid25v0000aeyjmxfwlc7t',
        'uuid':
            '76e0dcea-fe46-43e5-95f5-a5e3f378520a',
        'schemaId':
            'ckppid25v0000aeyjmxfwlc7t',
        'answers': [{
            'schemaId': 'ckppid25v0000aeyjmxfwlc7t',
        }, {
            'schemaId': 'ckppide010001aeyj0yhiaghc'
        }, {
            'schemaId': 'ckppidq4u0002aeyjmcc4toxw'
        }, {
            'schemaId': 'ckppie29m0003aeyjk1ixzcom'
        }]
    }],
                     predictions=[{
                         'uuid':
                             '76e0dcea-fe46-43e5-95f5-a5e3f378520a',
                         'schemaId':
                             'ckppid25v0000aeyjmxfwlc7t',
                         'dataRow': {
                             'id': 'ckppihxc10005aeyjen11h7jh'
                         },
                         'answers': [{
                             'schemaId': 'ckppid25v0000aeyjmxfwlc7t',
                         }, {
                             'schemaId': 'ckppide010001aeyj0yhiaghc'
                         }, {
                             'schemaId': 'ckppidq4u0002aeyjmcc4toxw'
                         }, {
                             'schemaId': 'ckppiebx80004aeyjuwvos69e'
                         }]
                     }],
                     expected=0.6)


@pytest.fixture
def partially_matching_checklist_2():
    return NameSpace(labels=[{
        'featureId':
            '1234567890111213141516171',
        'schemaId':
            'ckppid25v0000aeyjmxfwlc7t',
        'uuid':
            '76e0dcea-fe46-43e5-95f5-a5e3f378520a',
        'schemaId':
            'ckppid25v0000aeyjmxfwlc7t',
        'answers': [{
            'schemaId': 'ckppid25v0000aeyjmxfwlc7t',
        }, {
            'schemaId': 'ckppide010001aeyj0yhiaghc'
        }]
    }],
                     predictions=[{
                         'uuid':
                             '76e0dcea-fe46-43e5-95f5-a5e3f378520a',
                         'schemaId':
                             'ckppid25v0000aeyjmxfwlc7t',
                         'dataRow': {
                             'id': 'ckppihxc10005aeyjen11h7jh'
                         },
                         'answers': [{
                             'schemaId': 'ckppid25v0000aeyjmxfwlc7t',
                         }, {
                             'schemaId': 'ckppide010001aeyj0yhiaghc'
                         }, {
                             'schemaId': 'ckppidq4u0002aeyjmcc4toxw'
                         }, {
                             'schemaId': 'ckppiebx80004aeyjuwvos69e'
                         }]
                     }],
                     expected=0.5)


@pytest.fixture
def partially_matching_checklist_3():
    return NameSpace(labels=[{
        'featureId':
            '1234567890111213141516171',
        'schemaId':
            'ckppid25v0000aeyjmxfwlc7t',
        'uuid':
            '76e0dcea-fe46-43e5-95f5-a5e3f378520a',
        'schemaId':
            'ckppid25v0000aeyjmxfwlc7t',
        'answers': [{
            'schemaId': 'ckppid25v0000aeyjmxfwlc7t',
        }, {
            'schemaId': 'ckppide010001aeyj0yhiaghc'
        }, {
            'schemaId': 'ckppidq4u0002aeyjmcc4toxw'
        }, {
            'schemaId': 'ckppiebx80004aeyjuwvos69e'
        }]
    }],
                     predictions=[{
                         'uuid':
                             '76e0dcea-fe46-43e5-95f5-a5e3f378520a',
                         'schemaId':
                             'ckppid25v0000aeyjmxfwlc7t',
                         'dataRow': {
                             'id': 'ckppihxc10005aeyjen11h7jh'
                         },
                         'answers': [{
                             'schemaId': 'ckppid25v0000aeyjmxfwlc7t',
                         }, {
                             'schemaId': 'ckppide010001aeyj0yhiaghc'
                         }]
                     }],
                     expected=0.5)


@pytest.fixture
def empty_checklist_label():
    return NameSpace(labels=[],
                     predictions=[{
                         'uuid': '76e0dcea-fe46-43e5-95f5-a5e3f378520a',
                         'schemaId': 'ckppid25v0000aeyjmxfwlc7t',
                         'dataRow': {
                             'id': 'ckppihxc10005aeyjen11h7jh'
                         },
                         'answers': [{
                             'schemaId': 'ckppid25v0000aeyjmxfwlc7t'
                         }]
                     }],
                     expected=0)


@pytest.fixture
def empty_checklist_prediction():
    return NameSpace(labels=[{
        'featureId': '1234567890111213141516171',
        'schemaId': 'ckppid25v0000aeyjmxfwlc7t',
        'dataRow': {
            'id': 'ckppihxc10005aeyjen11h7jh'
        },
        'answers': [{
            'schemaId': 'ckppid25v0000aeyjmxfwlc7t'
        }]
    }],
                     predictions=[],
                     expected=0)


@pytest.fixture
def matching_text():
    return NameSpace(labels=[{
        'featureId': '1234567890111213141516171',
        'schemaId': 'ckppid25v0000aeyjmxfwlc7t',
        'answer': 'test'
    }],
                     predictions=[{
                         'uuid': '76e0dcea-fe46-43e5-95f5-a5e3f378520a',
                         'schemaId': 'ckppid25v0000aeyjmxfwlc7t',
                         'dataRow': {
                             'id': 'ckppihxc10005aeyjen11h7jh'
                         },
                         'answer': 'test'
                     }],
                     expected=1.0)


@pytest.fixture
def not_matching_text():
    return NameSpace(labels=[{
        'featureId': '1234567890111213141516171',
        'schemaId': 'ckppid25v0000aeyjmxfwlc7t',
        'answer': 'test'
    }],
                     predictions=[{
                         'uuid': '76e0dcea-fe46-43e5-95f5-a5e3f378520a',
                         'schemaId': 'ckppid25v0000aeyjmxfwlc7t',
                         'dataRow': {
                             'id': 'ckppihxc10005aeyjen11h7jh'
                         },
                         'answer': 'not_test'
                     }],
                     expected=0.)


@pytest.fixture
def test_box_with_subclass():
    return NameSpace(labels=[{
        'featureId':
            'ckppivl7p0006aeyj92cezr9d',
        'schemaId':
            'ckppid25v0000aeyjmxfwlc7t',
        "bbox": {
            "top": 1099,
            "left": 2010,
            "height": 690,
            "width": 591
        },
        'classifications': [{
            'schemaId': 'ckppid25v0000aeyjmxfwlc7t',
            'answer': 'test'
        }]
    }],
                     predictions=[{
                         'uuid':
                             '76e0dcea-fe46-43e5-95f5-a5e3f378520a',
                         'schemaId':
                             'ckppid25v0000aeyjmxfwlc7t',
                         'dataRow': {
                             'id': 'ckppihxc10005aeyjen11h7jh'
                         },
                         "bbox": {
                             "top": 1099,
                             "left": 2010,
                             "height": 690,
                             "width": 591
                         },
                         'classifications': [{
                             'schemaId': 'ckppid25v0000aeyjmxfwlc7t',
                             'answer': 'test'
                         }]
                     }],
                     expected=1.0)


@pytest.fixture
def test_box_with_wrong_subclass():
    return NameSpace(labels=[{
        'featureId':
            'ckppivl7p0006aeyj92cezr9d',
        'schemaId':
            'ckppid25v0000aeyjmxfwlc7t',
        "bbox": {
            "top": 1099,
            "left": 2010,
            "height": 690,
            "width": 591
        },
        'classifications': [{
            'schemaId': 'ckppid25v0000aeyjmxfwlc7t',
            'answer': 'test'
        }]
    }],
                     predictions=[{
                         'uuid':
                             '76e0dcea-fe46-43e5-95f5-a5e3f378520a',
                         'dataRow': {
                             'id': 'ckppihxc10005aeyjen11h7jh'
                         },
                         'schemaId':
                             'ckppid25v0000aeyjmxfwlc7t',
                         "bbox": {
                             "top": 1099,
                             "left": 2010,
                             "height": 690,
                             "width": 591
                         },
                         'classifications': [{
                             'schemaId': 'ckppid25v0000aeyjmxfwlc7t',
                             'answer': 'not_test'
                         }]
                     }],
                     expected=0.5)


@pytest.fixture
def line_pair():
    return NameSpace(labels=[{
        'featureId': 'ckppivl7p0006aeyj92cezr9d',
        'schemaId': 'ckppid25v0000aeyjmxfwlc7t',
        "line": [{
            "x": 0,
            "y": 100
        }, {
            "x": 0,
            "y": 0
        }],
    }],
                     predictions=[{
                         'uuid': '76e0dcea-fe46-43e5-95f5-a5e3f378520a',
                         'schemaId': 'ckppid25v0000aeyjmxfwlc7t',
                         'dataRow': {
                             'id': 'ckppihxc10005aeyjen11h7jh'
                         },
                         "line": [{
                             "x": 5,
                             "y": 95
                         }, {
                             "x": 0,
                             "y": 0
                         }],
                     }],
                     expected=0.9496975567603978)


@pytest.fixture
def point_pair():
    return NameSpace(labels=[{
        'featureId': 'ckppivl7p0006aeyj92cezr9d',
        'schemaId': 'ckppid25v0000aeyjmxfwlc7t',
        "point": {
            'x': 0,
            'y': 0
        }
    }],
                     predictions=[{
                         'dataRow': {
                             'id': 'ckppihxc10005aeyjen11h7jh'
                         },
                         'uuid': '76e0dcea-fe46-43e5-95f5-a5e3f378520a',
                         'schemaId': 'ckppid25v0000aeyjmxfwlc7t',
                         "point": {
                             'x': 5,
                             'y': 5
                         }
                     }],
                     expected=0.879113232477017)
