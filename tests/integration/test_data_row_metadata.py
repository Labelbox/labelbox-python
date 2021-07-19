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
def dr_md_ontology(client):
    yield client.get_datarow_metadata_ontology()


@pytest.fixture
def datarow(dataset: Dataset):
    task = dataset.create_data_rows([
        {
            "row_data": IMG_URL
        },
    ])
    task.wait_till_done()
    dr = next(dataset.data_rows())
    yield dr
    dr.delete()


@pytest.fixture
def big_dataset(dataset: Dataset):
    task = dataset.create_data_rows([
        {
            "row_data": IMG_URL
        },
    ] * 1000)
    task.wait_till_done()

    yield dataset
    dataset.delete()


def make_metadata(dr_id) -> DataRowMetadata:
    embeddings = [0.0] * 128
    msg = "my-message"
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


def test_get_datarow_metadata_ontology(dr_md_ontology):
    mdo = dr_md_ontology
    assert len(mdo.all_fields)
    assert len(mdo.reserved_fields)
    assert len(mdo.custom_fields) == 0


def test_get_datarow_metadata(datarow):
    """No metadata"""
    md = datarow.make_metadata
    assert not len(md["fields"])
    assert len(md)


def test_bulk_upsert_datarow_metadata(datarow, dr_md_ontology):
    assert not len(datarow.metadata["fields"])
    metadata = make_metadata(datarow.uid)
    dr_md_ontology.bulk_upsert([metadata])
    assert len(datarow.metadata["fields"])


@pytest.mark.slow
def test_large_bulk_upsert_datarow_metadata(big_dataset, dr_md_ontology):
    metadata = []
    for dr in big_dataset.export_data_rows():
        metadata.append(make_metadata(dr.uid))
    response = dr_md_ontology.bulk_upsert(metadata)
    assert response

    for dr in big_dataset.export_data_rows():
        assert len(dr.metadata["fields"])


def test_bulk_delete_datarow_metadata(datarow: DataRow, dr_md_ontology):
    """test bulk deletes for non non fields"""
    assert not len(datarow.metadata["fields"])
    metadata = make_metadata(datarow.uid)
    metadata.fields = [
        m for m in metadata.fields if m.schema_id != SPLIT_SCHEMA_ID
    ]
    dr_md_ontology.bulk_upsert([metadata])
    assert len(datarow.metadata["fields"])

    dr_md_ontology.bulk_delete([
        DeleteDataRowMetadata(data_row_id=datarow.uid,
                              fields=[m.schema_id for m in metadata.fields])
    ])
    assert not (len(datarow.metadata["fields"]))


def test_bulk_delete_datarow_enum_metadata(datarow: DataRow, dr_md_ontology):
    """test bulk deletes for non non fields"""
    assert not len(datarow.metadata["fields"])
    metadata = make_metadata(datarow.uid)
    metadata.fields = [
        m for m in metadata.fields if m.schema_id == SPLIT_SCHEMA_ID
    ]
    dr_md_ontology.bulk_upsert([metadata])
    assert len(datarow.metadata["fields"])

    dr_md_ontology.bulk_delete([
        DeleteDataRowMetadata(data_row_id=datarow.uid,
                              fields=[TEST_SPLIT_ID, SPLIT_SCHEMA_ID])
    ])
    assert not (len(datarow.metadata["fields"]))


def test_raise_enum_upsert_schema_error(datarow, dr_md_ontology):
    """Setting an option id as the schema id will raise a Value Error"""

    metadata = DataRowMetadata(data_row_id=datarow.uid,
                               fields=[
                                   DataRowMetadataField(schema_id=TEST_SPLIT_ID,
                                                        value=SPLIT_SCHEMA_ID),
                               ])
    with pytest.raises(ValueError):
        dr_md_ontology.bulk_upsert([metadata])


def test_upsert_non_existent_schema_id(datarow, dr_md_ontology):
    """Raise error on non-existent schema id"""
    metadata = DataRowMetadata(data_row_id=datarow.uid,
                               fields=[
                                   DataRowMetadataField(
                                       schema_id=FAKE_SCHEMA_ID,
                                       value="message"),
                               ])
    with pytest.raises(ValueError):
        dr_md_ontology.bulk_upsert([metadata])
