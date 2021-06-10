from attr import validate
from unittest.mock import patch
import math
import numpy as np

from labelbox.data.metrics.iou import datarow_miou


def check_iou(pair):
    assert datarow_miou(pair.labels, pair.predictions) == pair.expected


def test_overlapping(polygon_pair, box_pair, mask_pair):
    check_iou(polygon_pair)
    check_iou(box_pair)
    with patch('labelbox.data.metrics.iou.url_to_numpy',
               side_effect=lambda x: np.frombuffer(x.encode('utf-8'),
                                                   dtype=np.uint8).reshape(
                                                       (32, 32, 3))):
        check_iou(mask_pair)


def test_unmatched(unmatched_label, unmatched_prediction):
    check_iou(unmatched_label)
    check_iou(unmatched_prediction)


def test_radio(empty_radio_label, matching_radio, empty_radio_prediction):
    check_iou(empty_radio_label)
    check_iou(matching_radio)
    check_iou(empty_radio_prediction)


def test_checklist(matching_checklist, partially_matching_checklist_1,
                   partially_matching_checklist_2,
                   partially_matching_checklist_3, empty_checklist_label,
                   empty_checklist_prediction):
    check_iou(matching_checklist)
    check_iou(partially_matching_checklist_1)
    check_iou(partially_matching_checklist_2)
    check_iou(partially_matching_checklist_3)
    check_iou(empty_checklist_label)
    check_iou(empty_checklist_prediction)


def test_text(matching_text, not_matching_text):
    check_iou(matching_text)
    check_iou(not_matching_text)


def test_vector_with_subclass(test_box_with_wrong_subclass,
                              test_box_with_subclass):
    check_iou(test_box_with_wrong_subclass)
    check_iou(test_box_with_subclass)


def test_others(point_pair, line_pair):
    assert math.isclose(datarow_miou(point_pair.labels, point_pair.predictions),
                        point_pair.expected)
    assert math.isclose(datarow_miou(line_pair.labels, line_pair.predictions),
                        line_pair.expected)
