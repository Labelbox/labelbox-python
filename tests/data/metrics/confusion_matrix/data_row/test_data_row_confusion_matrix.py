from labelbox.data.metrics.confusion_matrix.confusion_matrix import confusion_matrix_metric
from labelbox.data.metrics.iou.iou import miou_metric
from pytest_cases import parametrize, fixture_ref
from unittest.mock import patch
import math
from pytest_cases import pytest_parametrize_plus, fixture_ref
import numpy as np
import base64

from labelbox.data.metrics.iou import data_row_miou, feature_miou_metric
from labelbox.data.serialization import NDJsonConverter, LBV1Converter
from labelbox.data.annotation_types import Label, ImageData, Mask




@pytest_parametrize_plus("tool_examples",
                         [
                          fixture_ref('polygon_pair'),
                          fixture_ref('rectangle_pair'),
                          fixture_ref('mask_pair'),
                          fixture_ref('line_pair'),
                          fixture_ref('point_pair')]
)
def test_overlapping_pairs(tool_examples):
    for example in tool_examples:
        score = confusion_matrix_metric(example.predictions, example.ground_truths)
        if len(example.expected) == 0:
            assert len(score) == 0
        else:
            assert score[0].value == tuple(example.expected), f"{example.predictions},{example.ground_truths}"


