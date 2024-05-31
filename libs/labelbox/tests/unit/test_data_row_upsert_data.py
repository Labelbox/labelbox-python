import pytest
from labelbox.schema.internal.data_row_upsert_item import (DataRowUpsertItem)
from labelbox.schema.identifiable import UniqueId, GlobalKey
from labelbox.schema.asset_attachment import AttachmentType


@pytest.fixture
def data_row_create_items():
    dataset_id = 'test_dataset'
    items = [
        {
            "row_data": "http://my_site.com/photos/img_01.jpg",
            "global_key": "global_key1",
            "external_id": "ex_id1",
            "attachments": [{
                "type": AttachmentType.RAW_TEXT,
                "name": "att1",
                "value": "test1"
            }],
            "metadata": [{
                "name": "tag",
                "value": "tag value"
            },]
        },
    ]
    return dataset_id, items


@pytest.fixture
def data_row_update_items():
    dataset_id = 'test_dataset'
    items = [
        {
            "key": GlobalKey("global_key1"),
            "global_key": "global_key1_updated"
        },
        {
            "key": UniqueId('unique_id1'),
            "external_id": "ex_id1_updated"
        },
    ]
    return dataset_id, items


def test_data_row_upsert_items(data_row_create_items, data_row_update_items):
    dataset_id, create_items = data_row_create_items
    dataset_id, update_items = data_row_update_items
    items = create_items + update_items
    result = DataRowUpsertItem.build(dataset_id, items, (UniqueId, GlobalKey))
    assert len(result) == len(items)
    for item, res in zip(items, result):
        assert res.payload == item


def test_data_row_create_items(data_row_create_items):
    dataset_id, items = data_row_create_items
    result = DataRowUpsertItem.build(dataset_id, items)
    assert len(result) == len(items)
    for item, res in zip(items, result):
        assert res.payload == item


def test_data_row_create_items_not_updateable(data_row_update_items):
    dataset_id, items = data_row_update_items
    with pytest.raises(ValueError):
        DataRowUpsertItem.build(dataset_id, items, ())
