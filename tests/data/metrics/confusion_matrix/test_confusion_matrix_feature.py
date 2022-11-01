from pytest_cases import fixture_ref
from pytest_cases import parametrize, fixture_ref

from labelbox.data.metrics.confusion_matrix.confusion_matrix import feature_confusion_matrix_metric


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
            metrics = feature_confusion_matrix_metric(
                example.ground_truths,
                example.predictions,
                include_subclasses=include_subclasses)

            metrics = {r.feature_name: list(r.value) for r in metrics}
            if len(getattr(example, expected_attr_name)) == 0:
                assert len(metrics) == 0
            else:
                assert metrics == getattr(
                    example, expected_attr_name
                ), f"{example.predictions},{example.ground_truths}"


@parametrize("tool_examples",
             [fixture_ref('checklist_pairs'),
              fixture_ref('radio_pairs')])
def test_overlapping_classifications(tool_examples):
    for example in tool_examples:

        metrics = feature_confusion_matrix_metric(example.ground_truths,
                                                  example.predictions)

        metrics = {r.feature_name: list(r.value) for r in metrics}
        if len(example.expected) == 0:
            assert len(metrics) == 0
        else:
            assert metrics == example.expected, f"{example.predictions},{example.ground_truths}"
