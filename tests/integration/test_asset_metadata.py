import pytest

from labelbox.schema.asset_attachment import AssetAttachment
from labelbox import AssetMetadata
from labelbox.exceptions import InvalidQueryError

IMG_URL = "https://picsum.photos/200/300"


def test_asset_metadata_crud(project, dataset):
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

    with pytest.raises(ValueError) as exc_info:
        data_row.create_metadata("NOT_SUPPORTED_TYPE", "Value")
    expected_types = {item.value for item in AssetMetadata.MetaType}
    assert str(exc_info.value) == \
        f"meta_type must be one of {expected_types}. Found NOT_SUPPORTED_TYPE"

    # Check that filtering and sorting is prettily disabled
    with pytest.raises(InvalidQueryError) as exc_info:
        data_row.metadata(where=AssetMetadata.meta_value == "x")
    assert exc_info.value.message == \
        "Relationship DataRow.metadata doesn't support filtering"
    with pytest.raises(InvalidQueryError) as exc_info:
        data_row.metadata(order_by=AssetMetadata.meta_value.asc)
    assert exc_info.value.message == \
        "Relationship DataRow.metadata doesn't support sorting"


def test_asset_attachment_crud(project, dataset):
    # must attach a dataset to a project before it can be queryable
    # due to permissions
    project.datasets.connect(dataset)
    data_row = dataset.create_data_row(row_data=IMG_URL)
    assert len(list(data_row.metadata())) == 0

    # Create
    asset = data_row.create_attachment(AssetAttachment.TEXT, "Value")
    assert asset.attachment_type == AssetAttachment.TEXT
    assert asset.attachment_value == "Value"
    assert len(list(data_row.metadata())) == 1

    with pytest.raises(ValueError) as exc_info:
        data_row.create_attachment("NOT_SUPPORTED_TYPE", "Value")
    expected_types = {item.value for item in AssetAttachment.AttachmentType}
    assert str(exc_info.value) == \
        f"meta_type must be one of {expected_types}. Found NOT_SUPPORTED_TYPE"

    # Check that filtering and sorting is prettily disabled
    with pytest.raises(InvalidQueryError) as exc_info:
        data_row.attachments(where=AssetAttachment.attachment_value == "x")
    assert exc_info.value.message == \
        "Relationship DataRow.attachments doesn't support filtering"
    with pytest.raises(InvalidQueryError) as exc_info:
        data_row.attachments(order_by=AssetAttachment.attachment_value.asc)
    assert exc_info.value.message == \
        "Relationship DataRow.attachments doesn't support sorting"
