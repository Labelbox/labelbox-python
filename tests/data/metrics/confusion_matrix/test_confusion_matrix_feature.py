from pytest_cases import fixture_ref
from pytest_cases import pytest_parametrize_plus, fixture_ref

from labelbox.data.metrics.confusion_matrix.confusion_matrix import feature_confusion_matrix_metric


@pytest_parametrize_plus("tool_examples", [
    fixture_ref('polygon_pairs'),
    fixture_ref('rectangle_pairs'),
    fixture_ref('mask_pairs'),
    fixture_ref('line_pairs'),
    fixture_ref('point_pairs')
])
def test_overlapping_objects(tool_examples):
    for example in tool_examples:
        metrics = feature_confusion_matrix_metric(example.predictions,
                                                  example.ground_truths)

        metrics = {r.feature_name: list(r.value) for r in metrics}
        if len(example.expected) == 0:
            assert len(metrics) == 0
        else:
            assert metrics == example.expected, f"{example.predictions},{example.ground_truths}"


@pytest_parametrize_plus(
    "tool_examples",
    [fixture_ref('checklist_pairs'),
     fixture_ref('radio_pairs')])
def test_overlapping_classifications(tool_examples):
    for example in tool_examples:

        metrics = feature_confusion_matrix_metric(example.predictions,
                                                  example.ground_truths)

        metrics = {r.feature_name: list(r.value) for r in metrics}
        if len(example.expected) == 0:
            assert len(metrics) == 0
        else:
            assert metrics == example.expected, f"{example.predictions},{example.ground_truths}"
