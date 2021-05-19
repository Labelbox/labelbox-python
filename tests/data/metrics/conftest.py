from io import BytesIO
from types import SimpleNamespace
import pytest
import numpy as np
from PIL import Image


@pytest.fixture
def polygon_pair():
    return SimpleNamespace(labels=[{
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
                           }])


@pytest.fixture
def box_pair():
    return SimpleNamespace(labels=[{
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
                           }])


@pytest.fixture
def unmatched_prediction():
    return SimpleNamespace(labels=[{
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
                           }])


@pytest.fixture
def unmatched_label():
    return SimpleNamespace(labels=[{
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
                           }])


def create_mask_url(indices, h, w):
    mask = np.zeros((h, w, 3), dtype=np.uint8)
    for idx in indices:
        mask[idx] = 1
    return mask


@pytest.fixture
def mask_pair():
    #* Use your own signed urls so that you can resign the data
    #* This is just to make the demo work
    return SimpleNamespace(
        labels=[{
            'featureId': 'asdasds1',
            'schemaId': '1234',
            'instanceURI': create_mask_url([(0, 0, 0), (0, 1, 0)], 32, 32)
        }],
        predictions=[{
            'uuid': '12345',
            'schemaId': '1234',
            'instanceURI': create_mask_url([(0, 0, 0)], 32, 32)
        }])
