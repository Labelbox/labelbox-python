import json

from labelbox.data.annotation_types.data.generic_data_row_data import (
    GenericDataRowData,
)
from labelbox.data.annotation_types.metrics.confusion_matrix import (
    ConfusionMatrixMetric,
)
from labelbox.data.serialization.ndjson.converter import NDJsonConverter
from labelbox.types import (
    Label,
    ScalarMetric,
    ScalarMetricAggregation,
    ConfusionMatrixAggregation,
)


def test_metric():
    with open("tests/data/assets/ndjson/metric_import.json", "r") as file:
        data = json.load(file)

    labels = [
        Label(
            data=GenericDataRowData(
                uid="ckrmdnqj4000007msh9p2a27r",
            ),
            annotations=[
                ScalarMetric(
                    value=0.1,
                    extra={"uuid": "a22bbf6e-b2da-4abe-9a11-df84759f7672"},
                    aggregation=ScalarMetricAggregation.ARITHMETIC_MEAN,
                )
            ],
        )
    ]

    res = list(NDJsonConverter.serialize(labels))
    assert res == data


def test_custom_scalar_metric():
    data = [
        {
            "uuid": "a22bbf6e-b2da-4abe-9a11-df84759f7672",
            "dataRow": {"id": "ckrmdnqj4000007msh9p2a27r"},
            "metricValue": 0.1,
            "metricName": "custom_iou",
            "featureName": "sample_class",
            "subclassName": "sample_subclass",
            "aggregation": "SUM",
        },
        {
            "uuid": "a22bbf6e-b2da-4abe-9a11-df84759f7673",
            "dataRow": {"id": "ckrmdnqj4000007msh9p2a27r"},
            "metricValue": 0.1,
            "metricName": "custom_iou",
            "featureName": "sample_class",
            "aggregation": "SUM",
        },
        {
            "uuid": "a22bbf6e-b2da-4abe-9a11-df84759f7674",
            "dataRow": {"id": "ckrmdnqj4000007msh9p2a27r"},
            "metricValue": {0.1: 0.1, 0.2: 0.5},
            "metricName": "custom_iou",
            "aggregation": "SUM",
        },
    ]

    labels = [
        Label(
            data=GenericDataRowData(
                uid="ckrmdnqj4000007msh9p2a27r",
            ),
            annotations=[
                ScalarMetric(
                    value=0.1,
                    feature_name="sample_class",
                    subclass_name="sample_subclass",
                    extra={"uuid": "a22bbf6e-b2da-4abe-9a11-df84759f7672"},
                    metric_name="custom_iou",
                    aggregation=ScalarMetricAggregation.SUM,
                ),
                ScalarMetric(
                    value=0.1,
                    feature_name="sample_class",
                    extra={"uuid": "a22bbf6e-b2da-4abe-9a11-df84759f7673"},
                    metric_name="custom_iou",
                    aggregation=ScalarMetricAggregation.SUM,
                ),
                ScalarMetric(
                    value={"0.1": 0.1, "0.2": 0.5},
                    extra={"uuid": "a22bbf6e-b2da-4abe-9a11-df84759f7674"},
                    metric_name="custom_iou",
                    aggregation=ScalarMetricAggregation.SUM,
                ),
            ],
        )
    ]

    res = list(NDJsonConverter.serialize(labels))

    assert res == data


def test_custom_confusion_matrix_metric():
    data = [
        {
            "uuid": "a22bbf6e-b2da-4abe-9a11-df84759f7672",
            "dataRow": {"id": "ckrmdnqj4000007msh9p2a27r"},
            "metricValue": (1, 1, 2, 3),
            "metricName": "50%_iou",
            "featureName": "sample_class",
            "subclassName": "sample_subclass",
            "aggregation": "CONFUSION_MATRIX",
        },
        {
            "uuid": "a22bbf6e-b2da-4abe-9a11-df84759f7673",
            "dataRow": {"id": "ckrmdnqj4000007msh9p2a27r"},
            "metricValue": (0, 1, 2, 5),
            "metricName": "50%_iou",
            "featureName": "sample_class",
            "aggregation": "CONFUSION_MATRIX",
        },
        {
            "uuid": "a22bbf6e-b2da-4abe-9a11-df84759f7674",
            "dataRow": {"id": "ckrmdnqj4000007msh9p2a27r"},
            "metricValue": {0.1: (0, 1, 2, 3), 0.2: (5, 3, 4, 3)},
            "metricName": "50%_iou",
            "aggregation": "CONFUSION_MATRIX",
        },
    ]

    labels = [
        Label(
            data=GenericDataRowData(
                uid="ckrmdnqj4000007msh9p2a27r",
            ),
            annotations=[
                ConfusionMatrixMetric(
                    value=(1, 1, 2, 3),
                    feature_name="sample_class",
                    subclass_name="sample_subclass",
                    extra={"uuid": "a22bbf6e-b2da-4abe-9a11-df84759f7672"},
                    metric_name="50%_iou",
                    aggregation=ConfusionMatrixAggregation.CONFUSION_MATRIX,
                ),
                ConfusionMatrixMetric(
                    value=(0, 1, 2, 5),
                    feature_name="sample_class",
                    extra={"uuid": "a22bbf6e-b2da-4abe-9a11-df84759f7673"},
                    metric_name="50%_iou",
                    aggregation=ConfusionMatrixAggregation.CONFUSION_MATRIX,
                ),
                ConfusionMatrixMetric(
                    value={0.1: (0, 1, 2, 3), 0.2: (5, 3, 4, 3)},
                    extra={"uuid": "a22bbf6e-b2da-4abe-9a11-df84759f7674"},
                    metric_name="50%_iou",
                    aggregation=ConfusionMatrixAggregation.CONFUSION_MATRIX,
                ),
            ],
        )
    ]

    res = list(NDJsonConverter.serialize(labels))

    assert data == res
