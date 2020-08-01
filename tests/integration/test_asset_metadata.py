import pytest

from labelbox import AssetMetadata
from labelbox.exceptions import InvalidQueryError

IMG_URL = "https://picsum.photos/200/300"


@pytest.mark.skip(reason='TODO: already failing')
def test_asset_metadata_crud(dataset, rand_gen):
    data_row = dataset.create_data_row(row_data=IMG_URL)
    assert len(list(data_row.metadata())) == 0

    # Create
    asset = data_row.create_metadata(AssetMetadata.TEXT, "Value")
    assert asset.meta_type == AssetMetadata.TEXT
    assert asset.meta_value == "Value"
    assert len(list(data_row.metadata())) == 1

    # Check that filtering and sorting is prettily disabled
    with pytest.raises(InvalidQueryError) as exc_info:
        data_row.metadata(where=AssetMetadata.meta_value == "x")
    assert exc_info.value.message == \
        "Relationship DataRow.metadata doesn't support filtering"
    with pytest.raises(InvalidQueryError) as exc_info:
        data_row.metadata(order_by=AssetMetadata.meta_value.asc)
    assert exc_info.value.message == \
        "Relationship DataRow.metadata doesn't support sorting"
