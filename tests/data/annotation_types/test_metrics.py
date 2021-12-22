from pydantic import ValidationError
import pytest

from labelbox.data.annotation_types.metrics import ConfusionMatrixAggregation, ScalarMetricAggregation
from labelbox.data.annotation_types.metrics import ConfusionMatrixMetric, ScalarMetric
from labelbox.data.annotation_types.collection import LabelList
from labelbox.data.annotation_types import ScalarMetric, Label, ImageData


def test_legacy_scalar_metric():
    value = 10
    metric = ScalarMetric(value=value)
    assert metric.value == value

    label = Label(data=ImageData(uid="ckrmd9q8g000009mg6vej7hzg",
                                 url="google.com"),
                  annotations=[metric])
    expected = {
        'data': {
            'external_id': None,
            'uid': 'ckrmd9q8g000009mg6vej7hzg',
            'im_bytes': None,
            'file_path': None,
            'url': 'google.com',
            'arr': None
        },
        'annotations': [{
            'value': 10.0,
            'extra': {},
        }],
        'extra': {},
        'uid': None
    }
    assert label.dict() == expected
    assert next(LabelList([label])).dict() == expected


# TODO: Test with confidence


@pytest.mark.parametrize('feature_name,subclass_name,aggregation,value', [
    ("cat", "orange", ScalarMetricAggregation.ARITHMETIC_MEAN, 0.5),
    ("cat", None, ScalarMetricAggregation.ARITHMETIC_MEAN, 0.5),
    (None, None, ScalarMetricAggregation.ARITHMETIC_MEAN, 0.5),
    (None, None, None, 0.5),
    ("cat", "orange", ScalarMetricAggregation.ARITHMETIC_MEAN, 0.5),
    ("cat", None, ScalarMetricAggregation.HARMONIC_MEAN, 0.5),
    (None, None, ScalarMetricAggregation.GEOMETRIC_MEAN, 0.5),
    (None, None, ScalarMetricAggregation.SUM, 0.5),
    ("cat", "orange", ScalarMetricAggregation.ARITHMETIC_MEAN, {
        0.1: 0.2,
        0.3: 0.5,
        0.4: 0.8
    }),
])
def test_custom_scalar_metric(feature_name, subclass_name, aggregation, value):
    kwargs = {'aggregation': aggregation} if aggregation is not None else {}
    metric = ScalarMetric(metric_name="iou",
                          value=value,
                          feature_name=feature_name,
                          subclass_name=subclass_name,
                          **kwargs)
    assert metric.value == value

    label = Label(data=ImageData(uid="ckrmd9q8g000009mg6vej7hzg",
                                 url="google.com"),
                  annotations=[metric])
    expected = {
        'data': {
            'external_id': None,
            'uid': 'ckrmd9q8g000009mg6vej7hzg',
            'im_bytes': None,
            'file_path': None,
            'url': 'google.com',
            'arr': None
        },
        'annotations': [{
            'value':
                value,
            'metric_name':
                'iou',
            **({
                'feature_name': feature_name
            } if feature_name else {}),
            **({
                'subclass_name': subclass_name
            } if subclass_name else {}), 'aggregation':
                aggregation or ScalarMetricAggregation.ARITHMETIC_MEAN,
            'extra': {}
        }],
        'extra': {},
        'uid': None
    }

    assert label.dict() == expected
    assert next(LabelList([label])).dict() == expected


@pytest.mark.parametrize('feature_name,subclass_name,aggregation,value', [
    ("cat", "orange", ConfusionMatrixAggregation.CONFUSION_MATRIX,
     (0, 1, 2, 3)),
    ("cat", None, ConfusionMatrixAggregation.CONFUSION_MATRIX, (0, 1, 2, 3)),
    (None, None, ConfusionMatrixAggregation.CONFUSION_MATRIX, (0, 1, 2, 3)),
    (None, None, None, (0, 1, 2, 3)),
    ("cat", "orange", ConfusionMatrixAggregation.CONFUSION_MATRIX, {
        0.1: (0, 1, 2, 3),
        0.3: (0, 1, 2, 3),
        0.4: (0, 1, 2, 3)
    }),
])
def test_custom_confusison_matrix_metric(feature_name, subclass_name,
                                         aggregation, value):
    kwargs = {'aggregation': aggregation} if aggregation is not None else {}
    metric = ConfusionMatrixMetric(metric_name="confusion_matrix_50_pct_iou",
                                   value=value,
                                   feature_name=feature_name,
                                   subclass_name=subclass_name,
                                   **kwargs)
    assert metric.value == value

    label = Label(data=ImageData(uid="ckrmd9q8g000009mg6vej7hzg",
                                 url="google.com"),
                  annotations=[metric])
    expected = {
        'data': {
            'external_id': None,
            'uid': 'ckrmd9q8g000009mg6vej7hzg',
            'im_bytes': None,
            'file_path': None,
            'url': 'google.com',
            'arr': None
        },
        'annotations': [{
            'value':
                value,
            'metric_name':
                'confusion_matrix_50_pct_iou',
            **({
                'feature_name': feature_name
            } if feature_name else {}),
            **({
                'subclass_name': subclass_name
            } if subclass_name else {}), 'aggregation':
                aggregation or ConfusionMatrixAggregation.CONFUSION_MATRIX,
            'extra': {}
        }],
        'extra': {},
        'uid': None
    }
    assert label.dict() == expected
    assert next(LabelList([label])).dict() == expected


def test_name_exists():
    # Name is only required for ConfusionMatrixMetric for now.
    with pytest.raises(ValidationError) as exc_info:
        metric = ConfusionMatrixMetric(value=[0, 1, 2, 3])
    assert "field required (type=value_error.missing)" in str(exc_info.value)


def test_invalid_aggregations():
    with pytest.raises(ValidationError) as exc_info:
        metric = ScalarMetric(
            metric_name="invalid aggregation",
            value=0.1,
            aggregation=ConfusionMatrixAggregation.CONFUSION_MATRIX)
    assert "value is not a valid enumeration member" in str(exc_info.value)
    with pytest.raises(ValidationError) as exc_info:
        metric = ConfusionMatrixMetric(metric_name="invalid aggregation",
                                       value=[0, 1, 2, 3],
                                       aggregation=ScalarMetricAggregation.SUM)
    assert "value is not a valid enumeration member" in str(exc_info.value)


def test_invalid_number_of_confidence_scores():
    with pytest.raises(ValidationError) as exc_info:
        metric = ScalarMetric(metric_name="too few scores", value={0.1: 0.1})
    assert "Number of confidence scores must be greater" in str(exc_info.value)
    with pytest.raises(ValidationError) as exc_info:
        metric = ConfusionMatrixMetric(metric_name="too few scores",
                                       value={0.1: [0, 1, 2, 3]})
    assert "Number of confidence scores must be greater" in str(exc_info.value)
    with pytest.raises(ValidationError) as exc_info:
        metric = ScalarMetric(metric_name="too many scores",
                              value={i / 20.: 0.1 for i in range(20)})
    assert "Number of confidence scores must be greater" in str(exc_info.value)
    with pytest.raises(ValidationError) as exc_info:
        metric = ConfusionMatrixMetric(
            metric_name="too many scores",
            value={i / 20.: [0, 1, 2, 3] for i in range(20)})
    assert "Number of confidence scores must be greater" in str(exc_info.value)
