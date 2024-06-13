from unittest.mock import MagicMock, patch

import pytest
from labelbox.schema.internal.data_row_upsert_item import (DataRowUpsertItem,
                                                           DataRowCreateItem)
from labelbox.schema.identifiable import UniqueId, GlobalKey
from labelbox.schema.asset_attachment import AttachmentType
from labelbox.schema.dataset import Dataset
from labelbox.schema.internal.descriptor_file_creator import DescriptorFileCreator
from labelbox.schema.data_row import DataRow


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
def data_row_create_items_row_data_none():
    dataset_id = 'test_dataset'
    items = [
        {
            "row_data": None,
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
    result = DataRowUpsertItem.build(dataset_id, items)
    assert len(result) == len(items)
    for item, res in zip(items, result):
        assert res.payload == item


def test_data_row_create_items(data_row_create_items):
    dataset_id, items = data_row_create_items
    result = DataRowCreateItem.build(dataset_id, items)
    assert len(result) == len(items)
    for item, res in zip(items, result):
        assert res.payload == item


def test_data_row_create_items_not_updateable(data_row_update_items):
    dataset_id, items = data_row_update_items
    with pytest.raises(ValueError):
        DataRowCreateItem.build(dataset_id, items)


def test_upsert_is_empty():
    item = DataRowUpsertItem(id={
        "id": UniqueId,
        "value": UniqueId("123")
    },
                             payload={})
    assert item.is_empty()

    item = DataRowUpsertItem(id={
        "id": UniqueId,
        "value": UniqueId("123")
    },
                             payload={"dataset_id": "test_dataset"})
    assert item.is_empty()

    item = DataRowUpsertItem(
        id={}, payload={"row_data": "http://my_site.com/photos/img_01.jpg"})
    assert not item.is_empty()


def test_create_is_empty():
    item = DataRowCreateItem(id={}, payload={})
    assert item.is_empty()

    item = DataRowCreateItem(id={}, payload={"dataset_id": "test_dataset"})
    assert item.is_empty()

    item = DataRowCreateItem(id={}, payload={"row_data": None})
    assert item.is_empty()

    item = DataRowCreateItem(id={}, payload={"row_data": ""})
    assert item.is_empty()

    item = DataRowCreateItem(
        id={}, payload={"row_data": "http://my_site.com/photos/img_01.jpg"})
    assert not item.is_empty()

    item = DataRowCreateItem(
        id={},
        payload={DataRow.row_data: "http://my_site.com/photos/img_01.jpg"})
    assert not item.is_empty()

    legacy_converstational_data_payload = {
        "externalId":
            "Convo-123",
        "type":
            "application/vnd.labelbox.conversational",
        "conversationalData": [{
            "messageId":
                "message-0",
            "content":
                "I love iphone! i just bought new iphone! :smiling_face_with_3_hearts: :calling:",
            "user": {
                "userId": "Bot 002",
                "name": "Bot"
            },
        }]
    }
    item = DataRowCreateItem(id={}, payload=legacy_converstational_data_payload)
    assert not item.is_empty()


def test_create_row_data_none():
    items = [
        {
            "row_data": None,
            "global_key": "global_key1",
        },
    ]
    client = MagicMock()
    dataset = Dataset(
        client, {
            "id": 'test_dataset',
            "name": 'test_dataset',
            "createdAt": "2021-06-01T00:00:00.000Z",
            "description": "test_dataset",
            "updatedAt": "2021-06-01T00:00:00.000Z",
            "rowCount": 0,
        })

    with patch.object(DescriptorFileCreator,
                      'create',
                      return_value=["http://bar.com/chunk_uri"]):
        with pytest.raises(ValueError,
                           match="Some items have an empty payload"):
            dataset.create_data_rows(items)

    client.execute.assert_not_called()
