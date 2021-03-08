import pytest

from labelbox import AssetMetadata
from labelbox.exceptions import InvalidQueryError

IMG_URL = "https://picsum.photos/200/300"


def test_asset_metadata_crud(project, dataset, rand_gen):
    # must attach a dataset to a project before it can be queryable
    # due to permissions
    project.datasets.connect(dataset)
    data_row = dataset.create_data_row(row_data=IMG_URL)
    assert len(list(data_row.metadata())) == 0

    # Create
    asset = data_row.create_metadata(AssetMetadata.TEXT, "Value")
    assert asset.meta_type == AssetMetadata.TEXT
    assert asset.meta_value == "Value"
    assert len(list(data_row.metadata())) == 1

    with pytest.raises(ValueError):
        data_row.create_metadata("NOT_SUPPORTED_TYPE", "Value")

    # Check that filtering and sorting is prettily disabled
    with pytest.raises(InvalidQueryError) as exc_info:
        data_row.metadata(where=AssetMetadata.meta_value == "x")
    assert exc_info.value.message == \
        "Relationship DataRow.metadata doesn't support filtering"
    with pytest.raises(InvalidQueryError) as exc_info:
        data_row.metadata(order_by=AssetMetadata.meta_value.asc)
    assert exc_info.value.message == \
        "Relationship DataRow.metadata doesn't support sorting"
