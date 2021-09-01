import pytest

from labelbox.data.annotation_types.metrics.aggregations import MetricAggregation
from labelbox.data.annotation_types.metrics.scalar import CustomScalarMetric
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


@pytest.mark.parametrize('feature_name,subclass_name,aggregation', [
    ("cat", "orange", MetricAggregation.ARITHMETIC_MEAN),
    ("cat", None, MetricAggregation.ARITHMETIC_MEAN),
    (None, None, MetricAggregation.ARITHMETIC_MEAN),
    (None, None, None),
    ("cat", "orange", MetricAggregation.ARITHMETIC_MEAN),
    ("cat", None, MetricAggregation.HARMONIC_MEAN),
    (None, None, MetricAggregation.GEOMETRIC_MEAN),
    (None, None, MetricAggregation.SUM),
])
def test_custom_scalar_metric(feature_name, subclass_name, aggregation):
    value = 0.5
    kwargs = {'aggregation': aggregation} if aggregation is not None else {}
    metric = CustomScalarMetric(metric_name="iou",
                                metric_value=value,
                                feature_name=feature_name,
                                subclass_name=subclass_name,
                                **kwargs)
    assert metric.metric_value == value

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
            'metric_value': value,
            'metric_name': 'iou',
            'feature_name': feature_name,
            'subclass_name': subclass_name,
            'aggregation': aggregation or MetricAggregation.ARITHMETIC_MEAN,
            'extra': {}
        }],
        'extra': {},
        'uid': None
    }
    assert label.dict() == expected
    next(LabelList([label])).dict() == expected
