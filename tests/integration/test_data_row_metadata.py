from datetime import datetime

import pytest

from labelbox import DataRow, Dataset
from labelbox.schema.data_row_metadata import DataRowMetadataField, DataRowMetadata, DeleteDataRowMetadata, \
    DataRowMetadataOntology

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
def big_dataset(dataset: Dataset, image_url):
    task = dataset.create_data_rows([
        {
            "row_data": image_url,
            "external_id": "my-image"
        },
    ] * 250)
    task.wait_till_done()

    yield dataset
    dataset.delete()


def make_metadata(dr_id) -> DataRowMetadata:
    embeddings = [0.0] * 128
    msg = "A message"
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


def test_bulk_upsert_datarow_metadata(datarow, mdo: DataRowMetadataOntology):
    metadata = make_metadata(datarow.uid)
    mdo.bulk_upsert([metadata])
    assert len(mdo.bulk_export([datarow.uid]))
    assert len(mdo.bulk_export([datarow.uid])[0].fields)


def test_parse_upsert_datarow_metadata(datarow, mdo: DataRowMetadataOntology):
    metadata = make_metadata(datarow.uid)
    mdo.bulk_upsert([metadata])
    assert mdo.bulk_export([datarow.uid])


@pytest.mark.slow
def test_large_bulk_upsert_datarow_metadata(big_dataset, mdo):
    metadata = []
    data_row_ids = []
    for dr in big_dataset.data_rows():
        metadata.append(make_metadata(dr.uid))
        data_row_ids.append(dr.uid)
    errors = mdo.bulk_upsert(metadata)
    assert len(errors) == 0

    metadata_lookup = {
        metadata.data_row_id: metadata
        for metadata in mdo.bulk_export(data_row_ids)
    }
    for data_row_id in data_row_ids:
        assert len(metadata_lookup.get(data_row_id).fields)


def test_bulk_delete_datarow_metadata(datarow, mdo):
    """test bulk deletes for all fields"""
    metadata = make_metadata(datarow.uid)
    mdo.bulk_upsert([metadata])

    assert len(mdo.bulk_export([datarow.uid])[0].fields)
    upload_ids = [m.schema_id for m in metadata.fields[:-2]]
    mdo.bulk_delete(
        [DeleteDataRowMetadata(data_row_id=datarow.uid, fields=upload_ids)])
    remaining_ids = set(
        [f.schema_id for f in mdo.bulk_export([datarow.uid])[0].fields])
    assert not len(remaining_ids.intersection(set(upload_ids)))


def test_bulk_partial_delete_datarow_metadata(datarow, mdo):
    """Delete a single from metadata"""
    n_fields = len(mdo.bulk_export([datarow.uid])[0].fields)
    metadata = make_metadata(datarow.uid)
    mdo.bulk_upsert([metadata])

    assert len(mdo.bulk_export(
        [datarow.uid])[0].fields) == (n_fields + len(metadata.fields))

    mdo.bulk_delete([
        DeleteDataRowMetadata(data_row_id=datarow.uid, fields=[TEXT_SCHEMA_ID])
    ])
    assert len(mdo.bulk_export(
        [datarow.uid])[0].fields) == (n_fields + len(metadata.fields) - 1)


def test_large_bulk_delete_datarow_metadata(big_dataset, mdo):
    metadata = []
    for dr in big_dataset.data_rows():
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
    for dr in big_dataset.data_rows():
        deletes.append(
            DeleteDataRowMetadata(
                data_row_id=dr.uid,
                fields=[
                    EMBEDDING_SCHEMA_ID,  #
                    CAPTURE_DT_SCHEMA_ID
                ]))

    errors = mdo.bulk_delete(deletes)
    assert len(errors) == 0
    for dr in big_dataset.data_rows():
        # 1 remaining because only the embeddings id overlaps
        assert len(mdo.bulk_export([dr.uid])[0].fields) == 1


def test_bulk_delete_datarow_enum_metadata(datarow: DataRow, mdo):
    """test bulk deletes for non non fields"""
    n_fields = len(mdo.bulk_export([datarow.uid])[0].fields)
    metadata = make_metadata(datarow.uid)
    metadata.fields = [
        m for m in metadata.fields if m.schema_id == SPLIT_SCHEMA_ID
    ]
    mdo.bulk_upsert([metadata])

    assert len(mdo.bulk_export([datarow.uid])[0].fields) == len(
        set([x.schema_id for x in metadata.fields] +
            [x.schema_id for x in mdo.bulk_export([datarow.uid])[0].fields]))

    mdo.bulk_delete([
        DeleteDataRowMetadata(data_row_id=datarow.uid, fields=[SPLIT_SCHEMA_ID])
    ])
    assert len(mdo.bulk_export([datarow.uid])[0].fields) == n_fields


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
    mdo.bulk_delete([
        DeleteDataRowMetadata(data_row_id=datarow.uid,
                              fields=[EMBEDDING_SCHEMA_ID])
    ])
    # No message is returned


@pytest.mark.slow
def test_large_bulk_delete_non_existent_schema_id(big_dataset, mdo):
    deletes = []
    n_fields_start = 0
    for idx, dr in enumerate(big_dataset.data_rows()):
        if idx == 0:
            n_fields_start = len(mdo.bulk_export([dr.uid])[0].fields)
        deletes.append(
            DeleteDataRowMetadata(data_row_id=dr.uid,
                                  fields=[EMBEDDING_SCHEMA_ID]))
    errors = mdo.bulk_delete(deletes)
    assert len(errors) == 0

    for dr in big_dataset.export_data_rows():
        assert len(mdo.bulk_export([dr.uid])[0].fields) == n_fields_start
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
