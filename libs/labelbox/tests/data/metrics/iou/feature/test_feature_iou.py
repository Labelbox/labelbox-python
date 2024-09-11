import math

from labelbox.data.metrics.iou.iou import miou_metric, feature_miou_metric


def check_iou(pair):
    one_metrics = miou_metric(pair.predictions, pair.ground_truths)
    metrics = feature_miou_metric(pair.predictions, pair.ground_truths)
    result = {metric.feature_name: metric.value for metric in metrics}
    assert len(set(pair.expected.keys()).difference(set(result.keys()))) == 0

    for key in result:
        assert math.isclose(result[key], pair.expected[key])

    for metric in metrics:
        assert metric.metric_name == "custom_iou"

    if len(pair.expected):
        assert len(one_metrics)
        one_metric = one_metrics[0]
        assert one_metric.value == sum(list(pair.expected.values())) / len(
            pair.expected
        )


def test_different_classes(different_classes):
    for pair in different_classes:
        check_iou(pair)


def test_empty_annotations(empty_annotations):
    for pair in empty_annotations:
        check_iou(pair)


def test_one_overlap_classes(one_overlap_class):
    for pair in one_overlap_class:
        check_iou(pair)
