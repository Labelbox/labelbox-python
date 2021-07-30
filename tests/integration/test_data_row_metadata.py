from datetime import datetime

import pytest

from labelbox import DataRow, Dataset
from labelbox.schema.data_row_metadata import DataRowMetadataField, DataRowMetadata, DeleteDataRowMetadata

IMG_URL = "https://picsum.photos/id/829/200/300"
FAKE_SCHEMA_ID = "0" * 25
SPLIT_SCHEMA_ID = "cko8sbczn0002h2dkdaxb5kal"
TRAIN_SPLIT_ID = "cko8sbscr0003h2dk04w86hof"
TEST_SPLIT_ID = "cko8scbz70005h2dkastwhgqt"
EMBEDDING_SCHEMA_ID = "ckpyije740000yxdk81pbgjdc"
TEXT_SCHEMA_ID = "cko8s9r5v0001h2dk9elqdidh"
CAPTURE_DT_SCHEMA_ID = "cko8sdzv70006h2dk8jg64zvb"


@pytest.fixture
def mdo(client):
    yield client.get_data_row_metadata_ontology()


@pytest.fixture
def big_dataset(dataset: Dataset):
    task = dataset.create_data_rows([
        {
            "row_data": IMG_URL,
            "external_id": "my-image"
        },
    ] * 1000)
    task.wait_till_done()

    yield dataset
    dataset.delete()


def make_metadata(dr_id) -> DataRowMetadata:
    embeddings = [0.0] * 128
    msg = "a" * 50 + "a"
    time = datetime.utcnow()

    metadata = DataRowMetadata(
        data_row_id=dr_id,
        fields=[
            DataRowMetadataField(schema_id=SPLIT_SCHEMA_ID,
                                 value=TEST_SPLIT_ID),
            DataRowMetadataField(schema_id=CAPTURE_DT_SCHEMA_ID, value=time),
            DataRowMetadataField(schema_id=TEXT_SCHEMA_ID, value=msg),
            DataRowMetadataField(schema_id=EMBEDDING_SCHEMA_ID,
                                 value=embeddings),
        ])
    return metadata


def test_get_datarow_metadata_ontology(mdo):
    assert len(mdo.all_fields)
    assert len(mdo.reserved_fields)
    assert len(mdo.custom_fields) == 0


def test_get_datarow_metadata(datarow):
    """No metadata"""
    md = datarow.metadata
    assert not len(md["fields"])
    assert len(md)


def test_bulk_upsert_datarow_metadata(datarow, mdo):
    assert not len(datarow.metadata["fields"])
    metadata = make_metadata(datarow.uid)
    mdo.bulk_upsert([metadata])
    assert len(datarow.metadata["fields"])


@pytest.mark.slow
def test_large_bulk_upsert_datarow_metadata(big_dataset, mdo):
    metadata = []
    for dr in big_dataset.export_data_rows():
        metadata.append(make_metadata(dr.uid))
    errors = mdo.bulk_upsert(metadata)
    assert len(errors) == 0

    for dr in big_dataset.export_data_rows():
        assert len(dr.metadata["fields"])
        break


def test_bulk_delete_datarow_metadata(datarow, mdo):
    """test bulk deletes for all fields

    TODO: this fails because of the enum validation issue

    """
    assert not len(datarow.metadata["fields"])

    metadata = make_metadata(datarow.uid)
    print(mdo.bulk_upsert([metadata]))

    assert len(datarow.metadata["fields"])

    mdo.bulk_delete([
        DeleteDataRowMetadata(data_row_id=datarow.uid,
                              fields=[m.schema_id for m in metadata.fields])
    ])

    assert not len(datarow.metadata["fields"])


def test_bulk_partial_delete_datarow_metadata(datarow, mdo):
    """Delete a single from metadata"""
    assert not len(datarow.metadata["fields"])

    metadata = make_metadata(datarow.uid)
    mdo.bulk_upsert([metadata])

    assert len(datarow.metadata["fields"])

    mdo.bulk_delete([
        DeleteDataRowMetadata(data_row_id=datarow.uid, fields=[TEXT_SCHEMA_ID])
    ])

    assert len(datarow.metadata["fields"]) == 4


@pytest.mark.slow
def test_large_bulk_delete_datarow_metadata(big_dataset, mdo):
    metadata = []
    for dr in big_dataset.export_data_rows():
        metadata.append(
            DataRowMetadata(data_row_id=dr.uid,
                            fields=[
                                DataRowMetadataField(
                                    schema_id=EMBEDDING_SCHEMA_ID,
                                    value=[0.1] * 128),
                                DataRowMetadataField(schema_id=TEXT_SCHEMA_ID,
                                                     value="test-message")
                            ]))
    errors = mdo.bulk_upsert(metadata)
    assert len(errors) == 0

    deletes = []
    for dr in big_dataset.export_data_rows():
        deletes.append(
            DeleteDataRowMetadata(
                data_row_id=dr.uid,
                fields=[
                    EMBEDDING_SCHEMA_ID,  #
                    CAPTURE_DT_SCHEMA_ID
                ]))

    errors = mdo.bulk_delete(deletes)
    assert len(errors) == 0
    for dr in big_dataset.export_data_rows():
        assert len(dr.metadata["fields"]) == 1
        break


def test_bulk_delete_datarow_enum_metadata(datarow: DataRow, mdo):
    """test bulk deletes for non non fields"""
    assert not len(datarow.metadata["fields"])
    metadata = make_metadata(datarow.uid)
    metadata.fields = [
        m for m in metadata.fields if m.schema_id == SPLIT_SCHEMA_ID
    ]
    mdo.bulk_upsert([metadata])
    assert len(datarow.metadata["fields"])

    mdo.bulk_delete([
        DeleteDataRowMetadata(data_row_id=datarow.uid, fields=[SPLIT_SCHEMA_ID])
    ])
    assert not len(datarow.metadata["fields"])


def test_raise_enum_upsert_schema_error(datarow, mdo):
    """Setting an option id as the schema id will raise a Value Error"""

    metadata = DataRowMetadata(data_row_id=datarow.uid,
                               fields=[
                                   DataRowMetadataField(schema_id=TEST_SPLIT_ID,
                                                        value=SPLIT_SCHEMA_ID),
                               ])
    with pytest.raises(ValueError):
        mdo.bulk_upsert([metadata])


def test_upsert_non_existent_schema_id(datarow, mdo):
    """Raise error on non-existent schema id"""
    metadata = DataRowMetadata(data_row_id=datarow.uid,
                               fields=[
                                   DataRowMetadataField(
                                       schema_id=FAKE_SCHEMA_ID,
                                       value="message"),
                               ])
    with pytest.raises(ValueError):
        mdo.bulk_upsert([metadata])


def test_delete_non_existent_schema_id(datarow, mdo):
    assert not len(datarow.metadata["fields"])
    mdo.bulk_delete([
        DeleteDataRowMetadata(data_row_id=datarow.uid,
                              fields=[EMBEDDING_SCHEMA_ID])
    ])
    # No message is returned


@pytest.mark.slow
def test_large_bulk_delete_non_existent_schema_id(big_dataset, mdo):
    deletes = []
    for dr in big_dataset.export_data_rows():
        deletes.append(
            DeleteDataRowMetadata(data_row_id=dr.uid,
                                  fields=[EMBEDDING_SCHEMA_ID]))
    errors = mdo.bulk_delete(deletes)
    assert len(errors) == 0

    for dr in big_dataset.export_data_rows():
        assert not len(dr.metadata["fields"])
        break


def test_parse_raw_metadata(mdo):
    example = {
        'dataRowId':
            'ckr6kkfx801ui0yrtg9fje8xh',
        'fields': [{
            'schemaId': 'cko8s9r5v0001h2dk9elqdidh',
            'value': 'my-new-message'
        }, {
            'schemaId': 'cko8sbczn0002h2dkdaxb5kal',
            'value': {}
        }, {
            'schemaId': 'cko8sbscr0003h2dk04w86hof',
            'value': {}
        }, {
            'schemaId': 'cko8sdzv70006h2dk8jg64zvb',
            'value': '2021-07-20T21:41:14.606710Z'
        }]
    }

    parsed = mdo.parse_metadata([example])
    assert len(parsed) == 1
    row = parsed[0]
    assert row.data_row_id == example["dataRowId"]
    assert len(row.fields) == 3
