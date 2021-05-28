from labelbox.data.metrics.iou import datarow_miou
from unittest.mock import patch
import math


def test_overlapping(polygon_pair, box_pair, mask_pair):
    assert datarow_miou(polygon_pair.labels, polygon_pair.predictions) == polygon_pair.expected
    assert datarow_miou(box_pair.labels, box_pair.predictions) == box_pair.expected
    with patch('labelbox.data.metrics.iou.url_to_numpy',
               side_effect=lambda x: x):
        assert datarow_miou(mask_pair.labels, mask_pair.predictions) == mask_pair.expected


def test_unmatched(unmatched_label, unmatched_prediction):
    assert datarow_miou(unmatched_prediction.labels, unmatched_prediction.predictions) == unmatched_prediction.expected
    assert datarow_miou(unmatched_label.labels, unmatched_label.predictions) == unmatched_label.expected


def test_radio(empty_radio_label, matching_radio, empty_radio_prediction):
    assert datarow_miou(empty_radio_label.labels, empty_radio_label.predictions) == empty_radio_label.expected
    assert datarow_miou(matching_radio.labels, matching_radio.predictions) == matching_radio.expected
    assert datarow_miou(empty_radio_prediction.labels, empty_radio_prediction.predictions) == empty_radio_prediction.expected

def test_checklist(matching_checklist, partially_matching_checklist_1,partially_matching_checklist_2,partially_matching_checklist_3, empty_checklist_label, empty_checklist_prediction):
    assert datarow_miou(matching_checklist.labels, matching_checklist.predictions) == matching_checklist.expected
    assert datarow_miou(partially_matching_checklist_1.labels, partially_matching_checklist_1.predictions) == partially_matching_checklist_1.expected
    assert datarow_miou(partially_matching_checklist_2.labels, partially_matching_checklist_2.predictions) == partially_matching_checklist_2.expected
    assert datarow_miou(partially_matching_checklist_3.labels, partially_matching_checklist_3.predictions) == partially_matching_checklist_3.expected
    assert datarow_miou(empty_checklist_label.labels, empty_checklist_label.predictions) == empty_checklist_label.expected
    assert datarow_miou(empty_checklist_prediction.labels, empty_checklist_prediction.predictions) == empty_checklist_prediction.expected

def test_text(matching_text, not_matching_text):
    assert datarow_miou(matching_text.labels, matching_text.predictions) == matching_text.expected
    assert datarow_miou(not_matching_text.labels, not_matching_text.predictions) == not_matching_text.expected


def test_vector_with_subclass(test_box_with_wrong_subclass, test_box_with_subclass):
    assert datarow_miou(test_box_with_wrong_subclass.labels, test_box_with_wrong_subclass.predictions) == test_box_with_wrong_subclass.expected
    assert datarow_miou(test_box_with_subclass.labels, test_box_with_subclass.predictions) == test_box_with_subclass.expected


def test_others(point_pair, line_pair):
    assert math.isclose(datarow_miou(point_pair.labels, point_pair.predictions), point_pair.expected)
    assert math.isclose(datarow_miou(line_pair.labels, line_pair.predictions), line_pair.expected)
