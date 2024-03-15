from io import BytesIO
from types import SimpleNamespace
import pytest
import numpy as np
from PIL import Image
import base64


class NameSpace(SimpleNamespace):

    def __init__(self,
                 predictions,
                 labels,
                 expected,
                 expected_without_subclasses=None,
                 data_row_expected=None,
                 media_attributes=None,
                 metadata=None,
                 classifications=None):
        super(NameSpace, self).__init__(
            predictions=predictions,
            labels={
                'DataRow ID': 'ckppihxc10005aeyjen11h7jh',
                'Labeled Data': "https://.jpg",
                'Media Attributes': media_attributes or {},
                'DataRow Metadata': metadata or [],
                'Label': {
                    'objects': labels,
                    'classifications': classifications or []
                }
            },
            expected=expected,
            expected_without_subclasses=expected_without_subclasses or expected,
            data_row_expected=data_row_expected)


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


def create_mask_url(indices, h, w, value):
    mask = np.zeros((h, w, 3), dtype=np.uint8)
    for idx in indices:
        mask[idx] = value
    return base64.b64encode(mask.tobytes()).decode('utf-8')


@pytest.fixture
def mask_pair():
    return NameSpace(labels=[{
        'featureId':
            '1234567890111213141516171',
        'schemaId':
            'ckppid25v0000aeyjmxfwlc7t',
        'instanceURI':
            create_mask_url([(0, 0), (0, 1)], 32, 32, (255, 255, 255))
    }],
                     predictions=[{
                         'uuid': '76e0dcea-fe46-43e5-95f5-a5e3f378520a',
                         'schemaId': 'ckppid25v0000aeyjmxfwlc7t',
                         'dataRow': {
                             'id': 'ckppihxc10005aeyjen11h7jh'
                         },
                         'mask': {
                             'instanceURI':
                                 create_mask_url([(0, 0)], 32, 32, (1, 1, 1)),
                             'colorRGB': (1, 1, 1)
                         }
                     }],
                     expected=0.5)


@pytest.fixture
def matching_radio():
    return NameSpace(labels=[],
                     classifications=[{
                         'featureId': '1234567890111213141516171',
                         'schemaId': 'ckrm02no8000008l3arwp6h4f',
                         'answer': {
                             'schemaId': 'ckppid25v0000aeyjmxfwlc7t'
                         }
                     }],
                     predictions=[{
                         'uuid': '76e0dcea-fe46-43e5-95f5-a5e3f378520a',
                         'schemaId': 'ckrm02no8000008l3arwp6h4f',
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
    return NameSpace(labels=[],
                     classifications=[{
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
    return NameSpace(labels=[],
                     classifications=[{
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
                     data_row_expected=1.,
                     expected={1.0: 3})


@pytest.fixture
def partially_matching_checklist_1():
    return NameSpace(labels=[],
                     classifications=[{
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
                     data_row_expected=0.6,
                     expected={
                         0.0: 2,
                         1.0: 3
                     })


@pytest.fixture
def partially_matching_checklist_2():
    return NameSpace(labels=[],
                     classifications=[{
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
                     data_row_expected=0.5,
                     expected={
                         1.0: 2,
                         0.0: 2
                     })


@pytest.fixture
def partially_matching_checklist_3():
    return NameSpace(labels=[],
                     classifications=[{
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
                     data_row_expected=0.5,
                     expected={
                         1.0: 2,
                         0.0: 2
                     })


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
                     data_row_expected=0.0,
                     expected={0.0: 1})


@pytest.fixture
def empty_checklist_prediction():
    return NameSpace(labels=[],
                     classifications=[{
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
                     data_row_expected=0.0,
                     expected={0.0: 1})


@pytest.fixture
def matching_text():
    return NameSpace(labels=[],
                     classifications=[{
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
    return NameSpace(labels=[],
                     classifications=[{
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
                     expected=0.5,
                     expected_without_subclasses=1.0)


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


@pytest.fixture
def matching_ner():
    return NameSpace(labels=[{
        'featureId': 'ckppivl7p0006aeyj92cezr9d',
        'schemaId': 'ckppid25v0000aeyjmxfwlc7t',
        'format': "text.location",
        'data': {
            "location": {
                "start": 0,
                "end": 10
            }
        }
    }],
                     predictions=[{
                         'dataRow': {
                             'id': 'ckppihxc10005aeyjen11h7jh'
                         },
                         'uuid': '76e0dcea-fe46-43e5-95f5-a5e3f378520a',
                         'schemaId': 'ckppid25v0000aeyjmxfwlc7t',
                         "location": {
                             "start": 0,
                             "end": 10
                         }
                     }],
                     expected=1)


@pytest.fixture
def no_matching_ner():
    return NameSpace(labels=[{
        'featureId': 'ckppivl7p0006aeyj92cezr9d',
        'schemaId': 'ckppid25v0000aeyjmxfwlc7t',
        'format': "text.location",
        'data': {
            "location": {
                "start": 0,
                "end": 5
            }
        }
    }],
                     predictions=[{
                         'dataRow': {
                             'id': 'ckppihxc10005aeyjen11h7jh'
                         },
                         'uuid': '76e0dcea-fe46-43e5-95f5-a5e3f378520a',
                         'schemaId': 'ckppid25v0000aeyjmxfwlc7t',
                         "location": {
                             "start": 5,
                             "end": 10
                         }
                     }],
                     expected=0)


@pytest.fixture
def partial_matching_ner():
    return NameSpace(labels=[{
        'featureId': 'ckppivl7p0006aeyj92cezr9d',
        'schemaId': 'ckppid25v0000aeyjmxfwlc7t',
        'format': "text.location",
        'data': {
            "location": {
                "start": 0,
                "end": 7
            }
        }
    }],
                     predictions=[{
                         'dataRow': {
                             'id': 'ckppihxc10005aeyjen11h7jh'
                         },
                         'uuid': '76e0dcea-fe46-43e5-95f5-a5e3f378520a',
                         'schemaId': 'ckppid25v0000aeyjmxfwlc7t',
                         "location": {
                             "start": 3,
                             "end": 5
                         }
                     }],
                     expected=0.2857142857142857)
