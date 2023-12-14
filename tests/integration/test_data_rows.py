from tempfile import NamedTemporaryFile
import time
import uuid
from datetime import datetime
import json
from labelbox.schema.media_type import MediaType

import pytest
import requests

from labelbox import DataRow
from labelbox.exceptions import MalformedQueryException
from labelbox.schema.task import Task
from labelbox.schema.data_row_metadata import DataRowMetadataField, DataRowMetadataKind
import labelbox.exceptions

SPLIT_SCHEMA_ID = "cko8sbczn0002h2dkdaxb5kal"
TEST_SPLIT_ID = "cko8scbz70005h2dkastwhgqt"
TEXT_SCHEMA_ID = "cko8s9r5v0001h2dk9elqdidh"
CAPTURE_DT_SCHEMA_ID = "cko8sdzv70006h2dk8jg64zvb"
EXPECTED_METADATA_SCHEMA_IDS = [
    SPLIT_SCHEMA_ID, TEST_SPLIT_ID, TEXT_SCHEMA_ID, CAPTURE_DT_SCHEMA_ID
].sort()
CUSTOM_TEXT_SCHEMA_NAME = "custom_text"


@pytest.fixture
def mdo(client):
    mdo = client.get_data_row_metadata_ontology()
    try:
        mdo.create_schema(CUSTOM_TEXT_SCHEMA_NAME, DataRowMetadataKind.string)
    except MalformedQueryException:
        # Do nothing if already exists
        pass
    mdo._raw_ontology = mdo._get_ontology()
    mdo._build_ontology()
    yield mdo


@pytest.fixture
def conversational_content():
    return {
        'row_data': {
            "messages": [{
                "messageId": "message-0",
                "timestampUsec": 1530718491,
                "content": "I love iphone! i just bought new iphone! 🥰 📲",
                "user": {
                    "userId": "Bot 002",
                    "name": "Bot"
                },
                "align": "left",
                "canLabel": False
            }],
            "version": 1,
            "type": "application/vnd.labelbox.conversational"
        }
    }


@pytest.fixture
def tile_content():
    return {
        "row_data": {
            "tileLayerUrl":
                "https://s3-us-west-1.amazonaws.com/lb-tiler-layers/mexico_city/{z}/{x}/{y}.png",
            "bounds": [[19.405662413477728, -99.21052827588443],
                       [19.400498983095076, -99.20534818927473]],
            "minZoom":
                12,
            "maxZoom":
                20,
            "epsg":
                "EPSG4326",
            "alternativeLayers": [{
                "tileLayerUrl":
                    "https://api.mapbox.com/styles/v1/mapbox/satellite-streets-v11/tiles/{z}/{x}/{y}?access_token=pk.eyJ1IjoibWFwYm94IiwiYSI6ImNpejY4NXVycTA2emYycXBndHRqcmZ3N3gifQ.rJcFIG214AriISLbB6B5aw",
                "name":
                    "Satellite"
            }, {
                "tileLayerUrl":
                    "https://api.mapbox.com/styles/v1/mapbox/navigation-guidance-night-v4/tiles/{z}/{x}/{y}?access_token=pk.eyJ1IjoibWFwYm94IiwiYSI6ImNpejY4NXVycTA2emYycXBndHRqcmZ3N3gifQ.rJcFIG214AriISLbB6B5aw",
                "name":
                    "Guidance"
            }]
        }
    }


def make_metadata_fields():
    msg = "A message"
    time = datetime.utcnow()

    fields = [
        DataRowMetadataField(schema_id=SPLIT_SCHEMA_ID, value=TEST_SPLIT_ID),
        DataRowMetadataField(schema_id=CAPTURE_DT_SCHEMA_ID, value=time),
        DataRowMetadataField(schema_id=TEXT_SCHEMA_ID, value=msg),
    ]
    return fields


def make_metadata_fields_dict():
    msg = "A message"
    time = datetime.utcnow()

    fields = [{
        "schema_id": SPLIT_SCHEMA_ID,
        "value": TEST_SPLIT_ID
    }, {
        "schema_id": CAPTURE_DT_SCHEMA_ID,
        "value": time
    }, {
        "schema_id": TEXT_SCHEMA_ID,
        "value": msg
    }]
    return fields


def test_get_data_row_by_global_key(data_row_and_global_key, client, rand_gen):
    _, global_key = data_row_and_global_key
    data_row = client.get_data_row_by_global_key(global_key)
    assert type(data_row) == DataRow
    assert data_row.global_key == global_key


def test_get_data_row(data_row, client):
    assert client.get_data_row(data_row.uid)


def test_lookup_data_rows(client, dataset):
    uid = str(uuid.uuid4())
    # 1 external id : 1 uid
    dr = dataset.create_data_row(row_data="123", external_id=uid)
    lookup = client.get_data_row_ids_for_external_ids([uid])
    assert len(lookup) == 1
    assert lookup[uid][0] == dr.uid
    # 2 external ids : 1 uid
    uid2 = str(uuid.uuid4())
    dr2 = dataset.create_data_row(row_data="123", external_id=uid2)
    lookup = client.get_data_row_ids_for_external_ids([uid, uid2])
    assert len(lookup) == 2
    assert all([len(x) == 1 for x in lookup.values()])
    assert lookup[uid][0] == dr.uid
    assert lookup[uid2][0] == dr2.uid
    # 1 external id : 2 uid
    dr3 = dataset.create_data_row(row_data="123", external_id=uid2)
    lookup = client.get_data_row_ids_for_external_ids([uid2])
    assert len(lookup) == 1
    assert len(lookup[uid2]) == 2
    assert lookup[uid2][0] == dr2.uid
    assert lookup[uid2][1] == dr3.uid
    # Empty args
    lookup = client.get_data_row_ids_for_external_ids([])
    assert len(lookup) == 0
    # Non matching
    lookup = client.get_data_row_ids_for_external_ids([str(uuid.uuid4())])
    assert len(lookup) == 0


def test_data_row_bulk_creation(dataset, rand_gen, image_url):
    client = dataset.client
    assert len(list(dataset.data_rows())) == 0

    # Test creation using URL
    task = dataset.create_data_rows([
        {
            DataRow.row_data: image_url
        },
        {
            "row_data": image_url
        },
    ])
    assert task in client.get_user().created_tasks()
    task.wait_till_done()
    assert task.status == "COMPLETE"

    data_rows = list(dataset.data_rows())
    assert len(data_rows) == 2
    assert {data_row.row_data for data_row in data_rows} == {image_url}
    assert {data_row.global_key for data_row in data_rows} == {None}

    data_rows = list(dataset.data_rows(from_cursor=data_rows[0].uid))
    assert len(data_rows) == 1

    # Test creation using file name
    with NamedTemporaryFile() as fp:
        data = rand_gen(str).encode()
        fp.write(data)
        fp.flush()
        task = dataset.create_data_rows([fp.name])
        task.wait_till_done()
        assert task.status == "COMPLETE"

        task = dataset.create_data_rows([{
            "row_data": fp.name,
            'external_id': 'some_name'
        }])
        task.wait_till_done()
        assert task.status == "COMPLETE"

        task = dataset.create_data_rows([{"row_data": fp.name}])
        task.wait_till_done()
        assert task.status == "COMPLETE"

    data_rows = list(dataset.data_rows())
    assert len(data_rows) == 5
    url = ({data_row.row_data for data_row in data_rows} - {image_url}).pop()
    assert requests.get(url).content == data

    for dr in data_rows:
        dr.delete()


@pytest.mark.slow
def test_data_row_large_bulk_creation(dataset, image_url):
    # Do a longer task and expect it not to be complete immediately
    n_urls = 1000
    n_local = 250
    with NamedTemporaryFile() as fp:
        fp.write("Test data".encode())
        fp.flush()
        task = dataset.create_data_rows([{
            DataRow.row_data: image_url
        }] * n_urls + [fp.name] * n_local)
    task.wait_till_done()
    assert task.status == "COMPLETE"
    assert len(list(dataset.data_rows())) == n_local + n_urls


def test_data_row_single_creation(dataset, rand_gen, image_url):
    client = dataset.client
    assert len(list(dataset.data_rows())) == 0

    data_row = dataset.create_data_row(row_data=image_url)
    assert len(list(dataset.data_rows())) == 1
    assert data_row.dataset() == dataset
    assert data_row.created_by() == client.get_user()
    assert data_row.organization() == client.get_organization()
    assert requests.get(image_url).content == \
        requests.get(data_row.row_data).content
    assert data_row.media_attributes is not None
    assert data_row.global_key is None

    with NamedTemporaryFile() as fp:
        data = rand_gen(str).encode()
        fp.write(data)
        fp.flush()
        data_row_2 = dataset.create_data_row(row_data=fp.name)
        assert len(list(dataset.data_rows())) == 2
        assert requests.get(data_row_2.row_data).content == data


def test_create_data_row_with_dict(dataset, image_url):
    client = dataset.client
    assert len(list(dataset.data_rows())) == 0
    dr = {"row_data": image_url}
    data_row = dataset.create_data_row(dr)
    assert len(list(dataset.data_rows())) == 1
    assert data_row.dataset() == dataset
    assert data_row.created_by() == client.get_user()
    assert data_row.organization() == client.get_organization()
    assert requests.get(image_url).content == \
        requests.get(data_row.row_data).content
    assert data_row.media_attributes is not None


def test_create_data_row_with_dict_containing_field(dataset, image_url):
    client = dataset.client
    assert len(list(dataset.data_rows())) == 0
    dr = {DataRow.row_data: image_url}
    data_row = dataset.create_data_row(dr)
    assert len(list(dataset.data_rows())) == 1
    assert data_row.dataset() == dataset
    assert data_row.created_by() == client.get_user()
    assert data_row.organization() == client.get_organization()
    assert requests.get(image_url).content == \
        requests.get(data_row.row_data).content
    assert data_row.media_attributes is not None


def test_create_data_row_with_dict_unpacked(dataset, image_url):
    client = dataset.client
    assert len(list(dataset.data_rows())) == 0
    dr = {"row_data": image_url}
    data_row = dataset.create_data_row(**dr)
    assert len(list(dataset.data_rows())) == 1
    assert data_row.dataset() == dataset
    assert data_row.created_by() == client.get_user()
    assert data_row.organization() == client.get_organization()
    assert requests.get(image_url).content == \
        requests.get(data_row.row_data).content
    assert data_row.media_attributes is not None


def test_create_data_row_with_invalid_input(dataset, image_url):
    with pytest.raises(labelbox.exceptions.InvalidQueryError) as exc:
        dataset.create_data_row("asdf")

    dr = {"row_data": image_url}
    with pytest.raises(labelbox.exceptions.InvalidQueryError) as exc:
        dataset.create_data_row(dr, row_data=image_url)


def test_create_data_row_with_metadata(mdo, dataset, image_url):
    client = dataset.client
    assert len(list(dataset.data_rows())) == 0

    data_row = dataset.create_data_row(row_data=image_url,
                                       metadata_fields=make_metadata_fields())

    assert len(list(dataset.data_rows())) == 1
    assert data_row.dataset() == dataset
    assert data_row.created_by() == client.get_user()
    assert data_row.organization() == client.get_organization()
    assert requests.get(image_url).content == \
        requests.get(data_row.row_data).content
    assert data_row.media_attributes is not None
    metadata_fields = data_row.metadata_fields
    metadata = data_row.metadata
    assert len(metadata_fields) == 3
    assert len(metadata) == 3
    assert [m["schemaId"] for m in metadata_fields
           ].sort() == EXPECTED_METADATA_SCHEMA_IDS
    for m in metadata:
        assert mdo._parse_upsert(m)


def test_create_data_row_with_metadata_dict(mdo, dataset, image_url):
    client = dataset.client
    assert len(list(dataset.data_rows())) == 0

    data_row = dataset.create_data_row(
        row_data=image_url, metadata_fields=make_metadata_fields_dict())

    assert len(list(dataset.data_rows())) == 1
    assert data_row.dataset() == dataset
    assert data_row.created_by() == client.get_user()
    assert data_row.organization() == client.get_organization()
    assert requests.get(image_url).content == \
        requests.get(data_row.row_data).content
    assert data_row.media_attributes is not None
    metadata_fields = data_row.metadata_fields
    metadata = data_row.metadata
    assert len(metadata_fields) == 3
    assert len(metadata) == 3
    assert [m["schemaId"] for m in metadata_fields
           ].sort() == EXPECTED_METADATA_SCHEMA_IDS
    for m in metadata:
        assert mdo._parse_upsert(m)


def test_create_data_row_with_invalid_metadata(dataset, image_url):
    fields = make_metadata_fields()
    # make the payload invalid by providing the same schema id more than once
    fields.append(
        DataRowMetadataField(schema_id=TEXT_SCHEMA_ID, value='some msg'))

    with pytest.raises(labelbox.exceptions.MalformedQueryException):
        dataset.create_data_row(row_data=image_url, metadata_fields=fields)


def test_create_data_rows_with_metadata(mdo, dataset, image_url):
    client = dataset.client
    assert len(list(dataset.data_rows())) == 0

    task = dataset.create_data_rows([
        {
            DataRow.row_data: image_url,
            DataRow.external_id: "row1",
            DataRow.metadata_fields: make_metadata_fields()
        },
        {
            DataRow.row_data: image_url,
            DataRow.external_id: "row2",
            "metadata_fields": make_metadata_fields()
        },
        {
            DataRow.row_data: image_url,
            DataRow.external_id: "row3",
            DataRow.metadata_fields: make_metadata_fields_dict()
        },
        {
            DataRow.row_data: image_url,
            DataRow.external_id: "row4",
            "metadata_fields": make_metadata_fields_dict()
        },
    ])
    task.wait_till_done()

    assert len(list(dataset.data_rows())) == 4
    for r in ["row1", "row2", "row3", "row4"]:
        row = list(dataset.data_rows(where=DataRow.external_id == r))[0]
        assert row.dataset() == dataset
        assert row.created_by() == client.get_user()
        assert row.organization() == client.get_organization()
        assert requests.get(image_url).content == \
            requests.get(row.row_data).content
        assert row.media_attributes is not None

        metadata_fields = row.metadata_fields
        metadata = row.metadata
        assert len(metadata_fields) == 3
        assert len(metadata) == 3
        assert [m["schemaId"] for m in metadata_fields
               ].sort() == EXPECTED_METADATA_SCHEMA_IDS
        for m in metadata:
            assert mdo._parse_upsert(m)


@pytest.mark.parametrize("test_function,metadata_obj_type",
                         [("create_data_rows", "class"),
                          ("create_data_rows", "dict"),
                          ("create_data_rows_sync", "class"),
                          ("create_data_rows_sync", "dict"),
                          ("create_data_row", "class"),
                          ("create_data_row", "dict")])
def test_create_data_rows_with_named_metadata_field_class(
        test_function, metadata_obj_type, mdo, dataset, image_url):

    row_with_metadata_field = {
        DataRow.row_data:
            image_url,
        DataRow.external_id:
            "row1",
        DataRow.metadata_fields: [
            DataRowMetadataField(name='split', value='test'),
            DataRowMetadataField(name=CUSTOM_TEXT_SCHEMA_NAME, value='hello')
        ]
    }

    row_with_metadata_dict = {
        DataRow.row_data:
            image_url,
        DataRow.external_id:
            "row2",
        "metadata_fields": [
            {
                'name': 'split',
                'value': 'test'
            },
            {
                'name': CUSTOM_TEXT_SCHEMA_NAME,
                'value': 'hello'
            },
        ]
    }

    assert len(list(dataset.data_rows())) == 0

    METADATA_FIELDS = {
        "class": row_with_metadata_field,
        "dict": row_with_metadata_dict
    }

    def create_data_row(data_rows):
        dataset.create_data_row(data_rows[0])

    CREATION_FUNCTION = {
        "create_data_rows": dataset.create_data_rows,
        "create_data_rows_sync": dataset.create_data_rows_sync,
        "create_data_row": create_data_row
    }
    data_rows = [METADATA_FIELDS[metadata_obj_type]]
    function_to_test = CREATION_FUNCTION[test_function]
    task = function_to_test(data_rows)

    if isinstance(task, Task):
        task.wait_till_done()

    created_rows = list(dataset.data_rows())
    assert len(created_rows) == 1
    assert len(created_rows[0].metadata_fields) == 2
    assert len(created_rows[0].metadata) == 2

    metadata = created_rows[0].metadata
    assert metadata[0].schema_id == SPLIT_SCHEMA_ID
    assert metadata[0].name == 'test'
    assert metadata[0].value == mdo.reserved_by_name['split']['test'].uid
    assert metadata[1].name == CUSTOM_TEXT_SCHEMA_NAME
    assert metadata[1].value == 'hello'
    assert metadata[1].schema_id == mdo.custom_by_name[
        CUSTOM_TEXT_SCHEMA_NAME].uid


def test_create_data_rows_with_invalid_metadata(dataset, image_url):
    fields = make_metadata_fields()
    # make the payload invalid by providing the same schema id more than once
    fields.append(
        DataRowMetadataField(schema_id=TEXT_SCHEMA_ID, value="some msg"))

    task = dataset.create_data_rows([{
        DataRow.row_data: image_url,
        DataRow.metadata_fields: fields
    }])
    task.wait_till_done(timeout_seconds=60)

    assert task.status == "COMPLETE"
    assert len(task.failed_data_rows) == 1
    assert f"A schemaId can only be specified once per DataRow : [{TEXT_SCHEMA_ID}]" in task.failed_data_rows[
        0]["message"]


def test_create_data_rows_with_metadata_missing_value(dataset, image_url):
    fields = make_metadata_fields()
    fields.append({"schemaId": "some schema id"})

    with pytest.raises(ValueError) as exc:
        dataset.create_data_rows([
            {
                DataRow.row_data: image_url,
                DataRow.external_id: "row1",
                DataRow.metadata_fields: fields
            },
        ])


def test_create_data_rows_with_metadata_missing_schema_id(dataset, image_url):
    fields = make_metadata_fields()
    fields.append({"value": "some value"})

    with pytest.raises(ValueError) as exc:
        dataset.create_data_rows([
            {
                DataRow.row_data: image_url,
                DataRow.external_id: "row1",
                DataRow.metadata_fields: fields
            },
        ])


def test_create_data_rows_with_metadata_wrong_type(dataset, image_url):
    fields = make_metadata_fields()
    fields.append("Neither DataRowMetadataField or dict")

    with pytest.raises(ValueError) as exc:
        task = dataset.create_data_rows([
            {
                DataRow.row_data: image_url,
                DataRow.external_id: "row1",
                DataRow.metadata_fields: fields
            },
        ])


def test_data_row_update(client, dataset, rand_gen, image_url,
                         wait_for_data_row_processing):
    external_id = rand_gen(str)
    data_row = dataset.create_data_row(row_data=image_url,
                                       external_id=external_id)
    assert data_row.external_id == external_id

    external_id_2 = rand_gen(str)
    data_row.update(external_id=external_id_2)
    assert data_row.external_id == external_id_2

    in_line_content = "123"
    data_row.update(row_data=in_line_content)
    assert data_row.row_data == in_line_content

    data_row.update(row_data=image_url)
    data_row = wait_for_data_row_processing(client, data_row)
    assert data_row.row_data == image_url

    # tileLayer becomes a media attribute
    pdf_url = "https://storage.googleapis.com/labelbox-datasets/arxiv-pdf/data/99-word-token-pdfs/0801.3483.pdf"
    tileLayerUrl = "https://storage.googleapis.com/labelbox-datasets/arxiv-pdf/data/99-word-token-pdfs/0801.3483-lb-textlayer.json"
    data_row.update(row_data={'pdfUrl': pdf_url, "tileLayerUrl": tileLayerUrl})
    data_row = wait_for_data_row_processing(client,
                                            data_row,
                                            compare_with_prev_media_attrs=True)
    assert data_row.row_data == pdf_url


def test_data_row_filtering_sorting(dataset, image_url):
    task = dataset.create_data_rows([
        {
            DataRow.row_data: image_url,
            DataRow.external_id: "row1"
        },
        {
            DataRow.row_data: image_url,
            DataRow.external_id: "row2"
        },
    ])
    task.wait_till_done()

    # Test filtering
    row1 = list(dataset.data_rows(where=DataRow.external_id == "row1"))
    assert len(row1) == 1
    row1 = dataset.data_rows_for_external_id("row1")
    assert len(row1) == 1
    row1 = row1[0]
    assert row1.external_id == "row1"
    row2 = list(dataset.data_rows(where=DataRow.external_id == "row2"))
    assert len(row2) == 1
    row2 = dataset.data_rows_for_external_id("row2")
    assert len(row2) == 1
    row2 = row2[0]
    assert row2.external_id == "row2"


@pytest.fixture
def create_datarows_for_data_row_deletion(dataset, image_url):
    task = dataset.create_data_rows([{
        DataRow.row_data: image_url,
        DataRow.external_id: str(i)
    } for i in range(10)])
    task.wait_till_done()

    data_rows = list(dataset.data_rows())

    yield data_rows
    for dr in data_rows:
        dr.delete()


def test_data_row_deletion(dataset, create_datarows_for_data_row_deletion):
    create_datarows_for_data_row_deletion
    data_rows = list(dataset.data_rows())
    expected = set(map(str, range(10)))
    assert {dr.external_id for dr in data_rows} == expected

    for dr in data_rows:
        if dr.external_id in "37":
            dr.delete()
    expected -= set("37")

    data_rows = list(dataset.data_rows())
    assert {dr.external_id for dr in data_rows} == expected

    DataRow.bulk_delete([dr for dr in data_rows if dr.external_id in "2458"])
    expected -= set("2458")

    data_rows = list(dataset.data_rows())
    assert {dr.external_id for dr in data_rows} == expected


def test_data_row_iteration(dataset, image_url) -> None:
    task = dataset.create_data_rows([
        {
            DataRow.row_data: image_url
        },
        {
            "row_data": image_url
        },
    ])
    task.wait_till_done()
    assert next(dataset.data_rows())


def test_data_row_attachments(dataset, image_url):
    attachments = [("IMAGE", image_url, "attachment image"),
                   ("RAW_TEXT", "test-text", None),
                   ("IMAGE_OVERLAY", image_url, "Overlay"),
                   ("HTML", image_url, None)]
    task = dataset.create_data_rows([{
        "row_data":
            image_url,
        "external_id":
            "test-id",
        "attachments": [{
            "type": attachment_type,
            "value": attachment_value,
            "name": attachment_name
        }]
    } for attachment_type, attachment_value, attachment_name in attachments])

    task.wait_till_done()
    assert task.status == "COMPLETE"
    data_rows = list(dataset.data_rows())
    assert len(data_rows) == len(attachments)
    for data_row in data_rows:
        assert len(list(data_row.attachments())) == 1
        assert data_row.external_id == "test-id"

    with pytest.raises(ValueError) as exc:
        task = dataset.create_data_rows([{
            "row_data": image_url,
            "external_id": "test-id",
            "attachments": [{
                "type": "INVALID",
                "value": "123"
            }]
        }])


def test_create_data_rows_sync_attachments(dataset, image_url):
    attachments = [("IMAGE", image_url, "image URL"),
                   ("RAW_TEXT", "test-text", None),
                   ("IMAGE_OVERLAY", image_url, "Overlay"),
                   ("HTML", image_url, None)]
    attachments_per_data_row = 3
    dataset.create_data_rows_sync([{
        "row_data":
            image_url,
        "external_id":
            "test-id",
        "attachments": [{
            "type": attachment_type,
            "value": attachment_value,
            "name": attachment_name
        } for _ in range(attachments_per_data_row)]
    } for attachment_type, attachment_value, attachment_name in attachments])
    data_rows = list(dataset.data_rows())
    assert len(data_rows) == len(attachments)
    for data_row in data_rows:
        assert len(list(data_row.attachments())) == attachments_per_data_row


def test_create_data_rows_sync_mixed_upload(dataset, image_url):
    n_local = 100
    n_urls = 100
    with NamedTemporaryFile() as fp:
        fp.write("Test data".encode())
        fp.flush()
        dataset.create_data_rows_sync([{
            DataRow.row_data: image_url
        }] * n_urls + [fp.name] * n_local)
    assert len(list(dataset.data_rows())) == n_local + n_urls


def test_delete_data_row_attachment(data_row, image_url):
    attachments = []

    # Anonymous attachment
    to_attach = [("IMAGE", image_url), ("RAW_TEXT", "test-text"),
                 ("IMAGE_OVERLAY", image_url), ("HTML", image_url)]
    for attachment_type, attachment_value in to_attach:
        attachments.append(
            data_row.create_attachment(attachment_type, attachment_value))

    # Attachment with a name
    to_attach = [("IMAGE", image_url, "Att. Image"),
                 ("RAW_TEXT", "test-text", "Att. Text"),
                 ("IMAGE_OVERLAY", image_url, "Image Overlay"),
                 ("HTML", image_url, "Att. HTML")]
    for attachment_type, attachment_value, attachment_name in to_attach:
        attachments.append(
            data_row.create_attachment(attachment_type, attachment_value,
                                       attachment_name))

    for attachment in attachments:
        attachment.delete()

    assert len(list(data_row.attachments())) == 0


def test_create_data_rows_result(client, dataset, image_url):
    task = dataset.create_data_rows([
        {
            DataRow.row_data: image_url,
            DataRow.external_id: "row1",
        },
        {
            DataRow.row_data: image_url,
            DataRow.external_id: "row1",
        },
    ])
    assert task.errors is None
    for result in task.result:
        client.get_data_row(result['id'])


def test_create_data_rows_local_file(dataset, sample_image):
    task = dataset.create_data_rows([{
        DataRow.row_data: sample_image,
        DataRow.metadata_fields: make_metadata_fields()
    }])
    task.wait_till_done()
    assert task.status == "COMPLETE"
    data_row = list(dataset.data_rows())[0]
    assert data_row.external_id == "tests/integration/media/sample_image.jpg"
    assert len(data_row.metadata_fields) == 3


def test_data_row_with_global_key(dataset, sample_image):
    global_key = str(uuid.uuid4())
    row = dataset.create_data_row({
        DataRow.row_data: sample_image,
        DataRow.global_key: global_key
    })

    assert row.global_key == global_key


def test_data_row_bulk_creation_with_unique_global_keys(dataset, sample_image):
    global_key_1 = str(uuid.uuid4())
    global_key_2 = str(uuid.uuid4())
    global_key_3 = str(uuid.uuid4())

    task = dataset.create_data_rows([
        {
            DataRow.row_data: sample_image,
            DataRow.global_key: global_key_1
        },
        {
            DataRow.row_data: sample_image,
            DataRow.global_key: global_key_2
        },
        {
            DataRow.row_data: sample_image,
            DataRow.global_key: global_key_3
        },
    ])

    task.wait_till_done()
    assert {row.global_key for row in dataset.data_rows()
           } == {global_key_1, global_key_2, global_key_3}


def test_data_row_bulk_creation_with_same_global_keys(dataset, sample_image,
                                                      snapshot):
    global_key_1 = str(uuid.uuid4())
    task = dataset.create_data_rows([{
        DataRow.row_data: sample_image,
        DataRow.global_key: global_key_1
    }, {
        DataRow.row_data: sample_image,
        DataRow.global_key: global_key_1
    }])

    task.wait_till_done()

    assert task.status == "COMPLETE"
    assert type(task.failed_data_rows) is list
    assert len(task.failed_data_rows) == 1
    assert type(task.created_data_rows) is list
    assert len(task.created_data_rows) == 1
    assert task.failed_data_rows[0][
        'message'] == f"Duplicate global key: '{global_key_1}'"
    assert task.failed_data_rows[0]['failedDataRows'][0][
        'externalId'] == sample_image
    assert task.created_data_rows[0]['externalId'] == sample_image
    assert task.created_data_rows[0]['globalKey'] == global_key_1


def test_data_row_delete_and_create_with_same_global_key(
        client, dataset, sample_image):
    global_key_1 = str(uuid.uuid4())
    data_row_payload = {
        DataRow.row_data: sample_image,
        DataRow.global_key: global_key_1
    }

    # should successfully insert new datarow
    task = dataset.create_data_rows([data_row_payload])
    task.wait_till_done()

    assert task.status == "COMPLETE"
    assert task.result[0]['global_key'] == global_key_1

    new_data_row_id = task.result[0]['id']

    # same payload should fail due to duplicated global key
    task = dataset.create_data_rows([data_row_payload])
    task.wait_till_done()

    assert task.status == "COMPLETE"
    assert len(task.failed_data_rows) == 1
    assert task.failed_data_rows[0][
        'message'] == f"Duplicate global key: '{global_key_1}'"

    # delete datarow
    client.get_data_row(new_data_row_id).delete()

    # should successfully insert new datarow now
    task = dataset.create_data_rows([data_row_payload])
    task.wait_till_done()

    assert task.status == "COMPLETE"
    assert task.result[0]['global_key'] == global_key_1


def test_data_row_bulk_creation_sync_with_unique_global_keys(
        dataset, sample_image):
    global_key_1 = str(uuid.uuid4())
    global_key_2 = str(uuid.uuid4())
    global_key_3 = str(uuid.uuid4())

    dataset.create_data_rows_sync([
        {
            DataRow.row_data: sample_image,
            DataRow.global_key: global_key_1
        },
        {
            DataRow.row_data: sample_image,
            DataRow.global_key: global_key_2
        },
        {
            DataRow.row_data: sample_image,
            DataRow.global_key: global_key_3
        },
    ])

    assert {row.global_key for row in dataset.data_rows()
           } == {global_key_1, global_key_2, global_key_3}


def test_data_row_bulk_creation_sync_with_same_global_keys(
        dataset, sample_image):
    global_key_1 = str(uuid.uuid4())

    with pytest.raises(labelbox.exceptions.MalformedQueryException) as exc_info:
        dataset.create_data_rows_sync([{
            DataRow.row_data: sample_image,
            DataRow.global_key: global_key_1
        }, {
            DataRow.row_data: sample_image,
            DataRow.global_key: global_key_1
        }])

    assert len(list(dataset.data_rows())) == 1
    assert list(dataset.data_rows())[0].global_key == global_key_1
    assert "Some data rows were not imported. Check error output here" in str(
        exc_info.value)


@pytest.fixture
def converstational_data_rows(dataset, conversational_content):
    examples = [
        {
            **conversational_content, 'media_type':
                MediaType.Conversational.value
        },
        conversational_content,
        {
            "conversationalData": conversational_content['row_data']['messages']
        }  # Old way to check for backwards compatibility
    ]
    task = dataset.create_data_rows(examples)
    task.wait_till_done()
    assert task.status == "COMPLETE"

    data_rows = list(dataset.data_rows())

    yield data_rows
    for dr in data_rows:
        dr.delete()


def test_create_conversational_text(converstational_data_rows,
                                    conversational_content):
    data_rows = converstational_data_rows
    for data_row in data_rows:
        assert requests.get(
            data_row.row_data).json() == conversational_content['row_data']


def test_invalid_media_type(dataset, conversational_content):
    for _, __ in [["Found invalid contents for media type: 'IMAGE'", 'IMAGE'],
                  [
                      "Found invalid media type: 'totallyinvalid'",
                      'totallyinvalid'
                  ]]:
        # TODO: What error kind should this be? It looks like for global key we are
        # using malformed query. But for invalid contents in FileUploads we use InvalidQueryError
        with pytest.raises(labelbox.exceptions.InvalidQueryError):
            dataset.create_data_rows_sync([{
                **conversational_content, 'media_type': 'IMAGE'
            }])


def test_create_tiled_layer(dataset, tile_content):
    examples = [
        {
            **tile_content, 'media_type': 'TMS_GEO'
        },
        tile_content,
        # Old way to check for backwards compatibility
        tile_content['row_data']
    ]
    dataset.create_data_rows_sync(examples)
    data_rows = list(dataset.data_rows())
    assert len(data_rows) == len(examples)
    for data_row in data_rows:
        assert json.loads(data_row.row_data) == tile_content['row_data']


def test_create_data_row_with_attachments(dataset):
    attachment_value = 'attachment value'
    dr = dataset.create_data_row(row_data="123",
                                 attachments=[{
                                     'type': 'RAW_TEXT',
                                     'value': attachment_value
                                 }])
    attachments = list(dr.attachments())
    assert len(attachments) == 1


def test_create_data_row_with_media_type(dataset, image_url):
    with pytest.raises(labelbox.exceptions.InvalidQueryError) as exc:
        dr = dataset.create_data_row(
            row_data={'invalid_object': 'invalid_value'}, media_type="IMAGE")

    assert "Media type validation failed, expected: 'image/*', was: application/json" in str(
        exc.value)

    dataset.create_data_row(row_data=image_url, media_type="IMAGE")
