from tempfile import NamedTemporaryFile
import uuid
from datetime import datetime

import pytest
import requests

from labelbox import DataRow
from labelbox.schema.data_row_metadata import DataRowMetadataField
import labelbox.exceptions

SPLIT_SCHEMA_ID = "cko8sbczn0002h2dkdaxb5kal"
TEST_SPLIT_ID = "cko8scbz70005h2dkastwhgqt"
EMBEDDING_SCHEMA_ID = "ckpyije740000yxdk81pbgjdc"
TEXT_SCHEMA_ID = "cko8s9r5v0001h2dk9elqdidh"
CAPTURE_DT_SCHEMA_ID = "cko8sdzv70006h2dk8jg64zvb"
EXPECTED_METADATA_SCHEMA_IDS = [
    SPLIT_SCHEMA_ID, TEST_SPLIT_ID, EMBEDDING_SCHEMA_ID, TEXT_SCHEMA_ID,
    CAPTURE_DT_SCHEMA_ID
].sort()


@pytest.fixture
def mdo(client):
    mdo = client.get_data_row_metadata_ontology()
    mdo._raw_ontology = mdo._get_ontology()
    mdo._build_ontology()
    yield mdo


def make_metadata_fields():
    embeddings = [0.0] * 128
    msg = "A message"
    time = datetime.utcnow()

    fields = [
        DataRowMetadataField(schema_id=SPLIT_SCHEMA_ID, value=TEST_SPLIT_ID),
        DataRowMetadataField(schema_id=CAPTURE_DT_SCHEMA_ID, value=time),
        DataRowMetadataField(schema_id=TEXT_SCHEMA_ID, value=msg),
        DataRowMetadataField(schema_id=EMBEDDING_SCHEMA_ID, value=embeddings),
    ]
    return fields


def make_metadata_fields_dict():
    embeddings = [0.0] * 128
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
    }, {
        "schema_id": EMBEDDING_SCHEMA_ID,
        "value": embeddings
    }]
    return fields


def test_get_data_row(datarow, client):
    assert client.get_data_row(datarow.uid)


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
    #1 external id : 2 uid
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

    data_rows[0].delete()


@pytest.mark.slow
def test_data_row_large_bulk_creation(dataset, image_url):
    # Do a longer task and expect it not to be complete immediately
    n_local = 2000
    n_urls = 250
    with NamedTemporaryFile() as fp:
        fp.write("Test data".encode())
        fp.flush()
        task = dataset.create_data_rows([{
            DataRow.row_data: image_url
        }] * n_local + [fp.name] * n_urls)
    task.wait_till_done()
    assert task.status == "COMPLETE"
    assert len(list(dataset.export_data_rows())) == n_local + n_urls


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
    assert len(metadata_fields) == 4
    assert len(metadata) == 4
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
    assert len(metadata_fields) == 4
    assert len(metadata) == 4
    assert [m["schemaId"] for m in metadata_fields
           ].sort() == EXPECTED_METADATA_SCHEMA_IDS
    for m in metadata:
        assert mdo._parse_upsert(m)


def test_create_data_row_with_invalid_metadata(dataset, image_url):
    fields = make_metadata_fields()
    fields.append(
        DataRowMetadataField(schema_id=EMBEDDING_SCHEMA_ID, value=[0.0] * 128))

    with pytest.raises(labelbox.exceptions.MalformedQueryException) as excinfo:
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
        assert len(metadata_fields) == 4
        assert len(metadata) == 4
        assert [m["schemaId"] for m in metadata_fields
               ].sort() == EXPECTED_METADATA_SCHEMA_IDS
        for m in metadata:
            assert mdo._parse_upsert(m)


def test_create_data_rows_with_invalid_metadata(dataset, image_url):
    fields = make_metadata_fields()
    fields.append(
        DataRowMetadataField(schema_id=EMBEDDING_SCHEMA_ID, value=[0.0] * 128))

    task = dataset.create_data_rows([{
        DataRow.row_data: image_url,
        DataRow.metadata_fields: fields
    }])
    task.wait_till_done()
    assert task.status == "FAILED"


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


def test_data_row_update(dataset, rand_gen, image_url):
    external_id = rand_gen(str)
    data_row = dataset.create_data_row(row_data=image_url,
                                       external_id=external_id)
    assert data_row.external_id == external_id

    external_id_2 = rand_gen(str)
    data_row.update(external_id=external_id_2)
    assert data_row.external_id == external_id_2


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

    # Test sorting
    assert list(
        dataset.data_rows(order_by=DataRow.external_id.asc)) == [row1, row2]
    assert list(
        dataset.data_rows(order_by=DataRow.external_id.desc)) == [row2, row1]


def test_data_row_deletion(dataset, image_url):
    task = dataset.create_data_rows([{
        DataRow.row_data: image_url,
        DataRow.external_id: str(i)
    } for i in range(10)])
    task.wait_till_done()

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
    attachments = [("IMAGE", image_url), ("TEXT", "test-text"),
                   ("IMAGE_OVERLAY", image_url), ("HTML", image_url)]
    task = dataset.create_data_rows([{
        "row_data": image_url,
        "external_id": "test-id",
        "attachments": [{
            "type": attachment_type,
            "value": attachment_value
        }]
    } for attachment_type, attachment_value in attachments])

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
    attachments = [("IMAGE", image_url), ("TEXT", "test-text"),
                   ("IMAGE_OVERLAY", image_url), ("HTML", image_url)]
    attachments_per_data_row = 3
    dataset.create_data_rows_sync([{
        "row_data":
            image_url,
        "external_id":
            "test-id",
        "attachments": [{
            "type": attachment_type,
            "value": attachment_value
        } for _ in range(attachments_per_data_row)]
    } for attachment_type, attachment_value in attachments])
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


def test_delete_data_row_attachment(datarow, image_url):
    attachments = []
    to_attach = [("IMAGE", image_url), ("TEXT", "test-text"),
                 ("IMAGE_OVERLAY", image_url), ("HTML", image_url)]
    for attachment_type, attachment_value in to_attach:
        attachments.append(
            datarow.create_attachment(attachment_type, attachment_value))

    for attachment in attachments:
        attachment.delete()

    assert len(list(datarow.attachments())) == 0


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
    assert len(data_row.metadata_fields) == 4
