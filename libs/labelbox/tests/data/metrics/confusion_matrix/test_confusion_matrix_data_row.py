from pytest_cases import fixture_ref
from pytest_cases import parametrize, fixture_ref

from labelbox.data.metrics.confusion_matrix.confusion_matrix import confusion_matrix_metric


@parametrize("tool_examples", [
    fixture_ref('polygon_pairs'),
    fixture_ref('rectangle_pairs'),
    fixture_ref('mask_pairs'),
    fixture_ref('line_pairs'),
    fixture_ref('point_pairs'),
    fixture_ref('ner_pairs')
])
def test_overlapping_objects(tool_examples):
    for example in tool_examples:

        for include_subclasses, expected_attr_name in [[
                True, 'expected'
        ], [False, 'expected_without_subclasses']]:
            score = confusion_matrix_metric(
                example.ground_truths,
                example.predictions,
                include_subclasses=include_subclasses)

            if len(getattr(example, expected_attr_name)) == 0:
                assert len(score) == 0
            else:
                expected = [0, 0, 0, 0]
                for expected_values in getattr(example,
                                               expected_attr_name).values():
                    for idx in range(4):
                        expected[idx] += expected_values[idx]
                assert score[0].value == tuple(
                    expected), f"{example.predictions},{example.ground_truths}"


@parametrize("tool_examples",
             [fixture_ref('checklist_pairs'),
              fixture_ref('radio_pairs')])
def test_overlapping_classifications(tool_examples):
    for example in tool_examples:
        score = confusion_matrix_metric(example.ground_truths,
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
