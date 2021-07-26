from pytest_cases import parametrize, fixture_ref
from unittest.mock import patch
import math
import numpy as np
import base64

from labelbox.data.metrics.iou import data_row_miou
from labelbox.data.serialization import NDJsonConverter, LBV1Converter


def check_iou(pair):
    assert data_row_miou(next(LBV1Converter.deserialize(pair.labels)), next(NDJsonConverter.deserialize(pair.predictions)) ) == pair.expected


def strings_to_fixtures(strings):
    return [fixture_ref(x) for x in strings]


def test_overlapping(polygon_pair, box_pair, mask_pair):
    check_iou(polygon_pair)
    check_iou(box_pair)
    with patch('labelbox.data.metrics.iou.url_to_numpy',
               side_effect=lambda x: np.frombuffer(
                   base64.b64decode(x.encode('utf-8')), dtype=np.uint8).reshape(
                       (32, 32, 3))):
        check_iou(mask_pair)


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
    assert math.isclose(data_row_miou(pair.labels, pair.predictions),
                        pair.expected)
