import json

import pytest

from labelbox.data.serialization.labelbox_v1.converter import LBV1Converter


@pytest.mark.parametrize(
    "file_path", ['tests/data/assets/labelbox_v1/tiled_image_export.json'])
def test_image(file_path):
    """Tests against both Simple and non-Simple tiled image export data. 
    index-0 is non-Simple, index-1 is Simple
    """
    with open(file_path, 'r') as f:
        payload = json.load(f)

        collection = LBV1Converter.deserialize(payload)
        collection_as_list = collection.as_list()

        assert len(collection_as_list) == 2
        assert len(collection_as_list[0].annotations) == 6
        assert len(collection_as_list[1].annotations) == 8