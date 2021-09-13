from pytest_cases import fixture_ref
from pytest_cases import pytest_parametrize_plus, fixture_ref

from labelbox.data.metrics.confusion_matrix.confusion_matrix import confusion_matrix_metric


@pytest_parametrize_plus("tool_examples", [
    fixture_ref('polygon_pairs'),
    fixture_ref('rectangle_pairs'),
    fixture_ref('mask_pairs'),
    fixture_ref('line_pairs'),
    fixture_ref('point_pairs')
])
def test_overlapping_objects(tool_examples):
    for example in tool_examples:
        score = confusion_matrix_metric(example.predictions,
                                        example.ground_truths)

        if len(example.expected) == 0:
            assert len(score) == 0
        else:
            expected = [0, 0, 0, 0]
            for expected_values in example.expected.values():
                for idx in range(4):
                    expected[idx] += expected_values[idx]
            assert score[0].value == tuple(
                expected), f"{example.predictions},{example.ground_truths}"


@pytest_parametrize_plus(
    "tool_examples",
    [fixture_ref('checklist_pairs'),
     fixture_ref('radio_pairs')])
def test_overlapping_classifications(tool_examples):
    for example in tool_examples:
        score = confusion_matrix_metric(example.ground_truths,,
                                        example.predictions)
        if len(example.expected) == 0:
            assert len(score) == 0
        else:
            expected = [0, 0, 0, 0]
            for expected_values in example.expected.values():
                for idx in range(4):
                    expected[idx] += expected_values[idx]
            assert score[0].value == tuple(
                expected), f"{example.predictions},{example.ground_truths}"


def test_partial_overlap(pair_iou_thresholds):
    for example in pair_iou_thresholds:
        for iou in example.expected.keys():
            score = confusion_matrix_metric(example.predictions,
                                            example.ground_truths,
                                            iou=iou)
            assert score[0].value == tuple(
                example.expected[iou]
            ), f"{example.predictions},{example.ground_truths}"
