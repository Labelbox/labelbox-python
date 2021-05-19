from labelbox.data.metrics.iou import datarow_miou
from unittest.mock import patch


def test_overlapping(polygon_pair, box_pair, mask_pair):
    result = datarow_miou(polygon_pair.labels, polygon_pair.predictions)
    assert result == 0.5
    result = datarow_miou(box_pair.labels, box_pair.predictions)
    assert result == 1.0
    with patch('labelbox.data.metrics.iou.url_to_numpy',
               side_effect=lambda x: x):
        result = datarow_miou(mask_pair.labels, mask_pair.predictions)
        assert result == 0.5


def test_unmatched(unmatched_label, unmatched_prediction):
    result = datarow_miou(unmatched_prediction.labels,
                          unmatched_prediction.predictions)
    assert result == 0.25
    result = datarow_miou(unmatched_label.labels, unmatched_label.predictions)
    assert result == 0.25
