from labelbox.data.annotation_types.collection import LabelList
from labelbox.data.annotation_types import ScalarMetric, Label, ImageData


def test_scalar_metric():
    value = 10
    metric = ScalarMetric(value=value)
    assert metric.value == value

    label = Label(data=ImageData(uid="ckrmd9q8g000009mg6vej7hzg"),
                  annotations=[metric])
    expected = {
        'data': {
            'external_id': None,
            'uid': 'ckrmd9q8g000009mg6vej7hzg',
            'im_bytes': None,
            'file_path': None,
            'url': None,
            'arr': None
        },
        'annotations': [{
            'value': 10.0,
            'extra': {}
        }],
        'extra': {},
        'uid': None
    }
    assert label.dict() == expected
    next(LabelList([label])).dict() == expected
