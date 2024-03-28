import json

import pytest
from labelbox.data.annotation_types.geometry.polygon import Polygon
from labelbox.data.annotation_types.geometry.line import Line
from labelbox.data.annotation_types.geometry.point import Point
from labelbox.data.annotation_types.geometry.rectangle import Rectangle

from labelbox.data.serialization.labelbox_v1.converter import LBV1Converter
from labelbox.schema.bulk_import_request import Bbox


@pytest.mark.parametrize(
    "file_path", ['tests/data/assets/labelbox_v1/tiled_image_export.json'])
def test_image(file_path):
    """Tests against both Simple and non-Simple tiled image export data. 
    index-0 is non-Simple, index-1 is Simple
    """
    with open(file_path, 'r') as f:
        payload = json.load(f)

        collection = LBV1Converter.deserialize(payload)
        collection_as_list = list(collection)

        assert len(collection_as_list) == 2

        non_simple_annotations = collection_as_list[0].annotations
        assert len(non_simple_annotations) == 6
        expected_shapes = [Polygon, Point, Point, Point, Line, Rectangle]
        for idx in range(len(non_simple_annotations)):
            assert isinstance(non_simple_annotations[idx].value,
                              expected_shapes[idx])
        assert non_simple_annotations[-1].value.start.x == -99.36567524971268
        assert non_simple_annotations[-1].value.start.y == 19.34717117508651
        assert non_simple_annotations[-1].value.end.x == -99.3649886680726
        assert non_simple_annotations[-1].value.end.y == 19.41999425190506

        simple_annotations = collection_as_list[1].annotations
        assert len(simple_annotations) == 8
        expected_shapes = [
            Polygon, Point, Point, Point, Point, Point, Line, Rectangle
        ]
        for idx in range(len(simple_annotations)):
            assert isinstance(simple_annotations[idx].value,
                              expected_shapes[idx])
