from labelbox.data.metrics.iou.iou import miou_metric
from pytest_cases import parametrize, fixture_ref
from unittest.mock import patch
import math
import numpy as np
import base64

from labelbox.data.metrics.iou import data_row_miou, feature_miou_metric
from labelbox.data.serialization import NDJsonConverter, LBV1Converter
from labelbox.data.annotation_types import Label, ImageData, Mask


def check_iou(pair, mask=None):
    default = Label(data=ImageData(uid="ckppihxc10005aeyjen11h7jh", url=''))
    prediction = next(NDJsonConverter.deserialize(pair.predictions), default)
    label = next(LBV1Converter.deserialize(
        [pair.labels]))  #we are messing up the prediction here somehow
    if mask:
        for annotation in [*prediction.annotations, *label.annotations]:
            if isinstance(annotation.value, Mask):
                annotation.value.mask.arr = np.frombuffer(
                    base64.b64decode(annotation.value.mask.url.encode('utf-8')),
                    dtype=np.uint8).reshape((32, 32, 3))
    assert math.isclose(data_row_miou(label, prediction), pair.expected)
    assert math.isclose(
        miou_metric(label.annotations, prediction.annotations)[0].value,
        pair.expected)
    feature_ious = feature_miou_metric(label.annotations,
                                       prediction.annotations)
    assert len(feature_ious
              ) == 1  # The tests run here should only have one class present.
    assert math.isclose(feature_ious[0].value, pair.expected)


def strings_to_fixtures(strings):
    return [fixture_ref(x) for x in strings]


def test_overlapping(polygon_pair, box_pair, mask_pair):
    check_iou(polygon_pair)
    check_iou(box_pair)
    check_iou(mask_pair, True)


@parametrize("pair",
             strings_to_fixtures([
                 "unmatched_label",
                 "unmatched_prediction",
             ]))
def test_unmatched(pair):
    check_iou(pair)


@parametrize("pair",
             strings_to_fixtures([
                 "empty_radio_label",
                 "matching_radio",
                 "empty_radio_prediction",
             ]))
def test_radio(pair):
    check_iou(pair)


@parametrize("pair",
             strings_to_fixtures([
                 "matching_checklist",
                 "partially_matching_checklist_1",
                 "partially_matching_checklist_2",
                 "partially_matching_checklist_3",
                 "empty_checklist_label",
                 "empty_checklist_prediction",
             ]))
def test_checklist(pair):
    check_iou(pair)


@parametrize("pair", strings_to_fixtures(["matching_text",
                                          "not_matching_text"]))
def test_text(pair):
    check_iou(pair)


@parametrize("pair",
             strings_to_fixtures(
                 ["test_box_with_wrong_subclass", "test_box_with_subclass"]))
def test_vector_with_subclass(pair):
    check_iou(pair)


@parametrize("pair", strings_to_fixtures(["point_pair", "line_pair"]))
def test_others(pair):
    check_iou(pair)
