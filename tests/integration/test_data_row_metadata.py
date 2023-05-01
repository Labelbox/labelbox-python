from datetime import datetime

import pytest
import uuid

from labelbox import DataRow, Dataset
from labelbox.exceptions import MalformedQueryException
from labelbox.schema.data_row_metadata import DataRowMetadataField, DataRowMetadata, DataRowMetadataKind, DeleteDataRowMetadata, \
    DataRowMetadataOntology, _parse_metadata_schema

INVALID_SCHEMA_ID = "1" * 25
FAKE_SCHEMA_ID = "0" * 25
FAKE_DATAROW_ID = "D" * 25
SPLIT_SCHEMA_ID = "cko8sbczn0002h2dkdaxb5kal"
TRAIN_SPLIT_ID = "cko8sbscr0003h2dk04w86hof"
TEST_SPLIT_ID = "cko8scbz70005h2dkastwhgqt"
TEXT_SCHEMA_ID = "cko8s9r5v0001h2dk9elqdidh"
CAPTURE_DT_SCHEMA_ID = "cko8sdzv70006h2dk8jg64zvb"
CUSTOM_TEXT_SCHEMA_NAME = 'custom_text'

FAKE_NUMBER_FIELD = {
    "id": FAKE_SCHEMA_ID,
    "name": "number",
    "kind": 'CustomMetadataNumber',
    "reserved": False
}


@pytest.fixture
def mdo(client):
    mdo = client.get_data_row_metadata_ontology()
    try:
        mdo.create_schema(CUSTOM_TEXT_SCHEMA_NAME, DataRowMetadataKind.string)
    except MalformedQueryException:
        # Do nothing if already exists
        pass
    mdo._raw_ontology = mdo._get_ontology()
    mdo._raw_ontology.append(FAKE_NUMBER_FIELD)
    mdo._build_ontology()
    yield mdo


@pytest.fixture
def big_dataset(dataset: Dataset, image_url):
    task = dataset.create_data_rows([
        {
            "row_data": image_url,
            "external_id": "my-image"
        },
    ] * 5)
    task.wait_till_done()

    yield dataset


def make_metadata(dr_id: str = None, gk: str = None) -> DataRowMetadata:
    msg = "A message"
    time = datetime.utcnow()

    metadata = DataRowMetadata(
        global_key=gk,
        data_row_id=dr_id,
        fields=[
            DataRowMetadataField(schema_id=SPLIT_SCHEMA_ID,
                                 value=TEST_SPLIT_ID),
            DataRowMetadataField(schema_id=CAPTURE_DT_SCHEMA_ID, value=time),
            DataRowMetadataField(schema_id=TEXT_SCHEMA_ID, value=msg),
        ])
    return metadata


def make_named_metadata(dr_id) -> DataRowMetadata:
    msg = "A message"
    time = datetime.utcnow()

    metadata = DataRowMetadata(data_row_id=dr_id,
                               fields=[
                                   DataRowMetadataField(name='split',
                                                        value=TEST_SPLIT_ID),
                                   DataRowMetadataField(name='captureDateTime',
                                                        value=time),
                                   DataRowMetadataField(
                                       name=CUSTOM_TEXT_SCHEMA_NAME, value=msg),
                               ])
    return metadata


def test_export_empty_metadata(client, configured_project_with_label,
                               wait_for_data_row_processing):
    project, _, data_row, _ = configured_project_with_label
    data_row = wait_for_data_row_processing(client, data_row)
    labels = project.label_generator()
    label = next(labels)
    assert label.data.metadata == []


def test_get_datarow_metadata_ontology(mdo):
    assert len(mdo.fields)
    assert len(mdo.reserved_fields)
    # two are created by mdo fixture but there may be more
    assert len(mdo.custom_fields) >= 2

    split = mdo.reserved_by_name["split"]["train"]

    assert DataRowMetadata(
        data_row_id=FAKE_DATAROW_ID,
        fields=[
            DataRowMetadataField(
                schema_id=mdo.reserved_by_name["captureDateTime"].uid,
                value=datetime.utcnow(),
            ),
            DataRowMetadataField(schema_id=split.parent, value=split.uid),
            DataRowMetadataField(schema_id=mdo.reserved_by_name["tag"].uid,
                                 value="hello-world"),
        ])


def test_bulk_upsert_datarow_metadata(datarow, mdo: DataRowMetadataOntology):
    metadata = make_metadata(datarow.uid)
    mdo.bulk_upsert([metadata])
    exported = mdo.bulk_export([datarow.uid])
    assert len(exported)
    assert len([field for field in exported[0].fields]) == 3


def test_bulk_upsert_datarow_metadata_by_globalkey(
        data_rows, mdo: DataRowMetadataOntology):
    global_keys = [data_row.global_key for data_row in data_rows]
    metadata = [make_metadata(gk=global_key) for global_key in global_keys]
    errors = mdo.bulk_upsert(metadata)
    assert len(errors) == 0


@pytest.mark.slow
def test_large_bulk_upsert_datarow_metadata(big_dataset, mdo):
    metadata = []
    data_row_ids = [dr.uid for dr in big_dataset.data_rows()]
    for data_row_id in data_row_ids:
        metadata.append(make_metadata(data_row_id))
    errors = mdo.bulk_upsert(metadata)
    assert len(errors) == 0

    metadata_lookup = {
        metadata.data_row_id: metadata
        for metadata in mdo.bulk_export(data_row_ids)
    }
    for data_row_id in data_row_ids:
        assert len([f for f in metadata_lookup.get(data_row_id).fields
                   ]), metadata_lookup.get(data_row_id).fields


def test_upsert_datarow_metadata_by_name(datarow, mdo):
    metadata = [make_named_metadata(datarow.uid)]
    errors = mdo.bulk_upsert(metadata)
    assert len(errors) == 0

    metadata_lookup = {
        metadata.data_row_id: metadata
        for metadata in mdo.bulk_export([datarow.uid])
    }
    assert len([f for f in metadata_lookup.get(datarow.uid).fields
               ]), metadata_lookup.get(datarow.uid).fields


def test_upsert_datarow_metadata_option_by_name(datarow, mdo):
    metadata = DataRowMetadata(data_row_id=datarow.uid,
                               fields=[
                                   DataRowMetadataField(name='split',
                                                        value='test'),
                               ])
    errors = mdo.bulk_upsert([metadata])
    assert len(errors) == 0

    datarows = mdo.bulk_export([datarow.uid])
    assert len(datarows[0].fields) == 1
    metadata = datarows[0].fields[0]
    assert metadata.schema_id == SPLIT_SCHEMA_ID
    assert metadata.name == 'test'
    assert metadata.value == TEST_SPLIT_ID


def test_upsert_datarow_metadata_option_by_incorrect_name(datarow, mdo):
    metadata = DataRowMetadata(data_row_id=datarow.uid,
                               fields=[
                                   DataRowMetadataField(name='split',
                                                        value='test1'),
                               ])
    with pytest.raises(KeyError):
        mdo.bulk_upsert([metadata])


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
    fields = [f for f in mdo.bulk_export([datarow.uid])[0].fields]
    assert len(fields) == (len(metadata.fields) - 1)


def test_large_bulk_delete_datarow_metadata(big_dataset, mdo):
    metadata = []
    data_row_ids = [dr.uid for dr in big_dataset.data_rows()]
    for data_row_id in data_row_ids:
        metadata.append(
            DataRowMetadata(data_row_id=data_row_id,
                            fields=[
                                DataRowMetadataField(schema_id=SPLIT_SCHEMA_ID,
                                                     value=TEST_SPLIT_ID),
                                DataRowMetadataField(schema_id=TEXT_SCHEMA_ID,
                                                     value="test-message")
                            ]))
    errors = mdo.bulk_upsert(metadata)
    assert len(errors) == 0

    deletes = []
    for data_row_id in data_row_ids:
        deletes.append(
            DeleteDataRowMetadata(
                data_row_id=data_row_id,
                fields=[SPLIT_SCHEMA_ID, CAPTURE_DT_SCHEMA_ID]))
    errors = mdo.bulk_delete(deletes)
    assert len(errors) == 0
    for data_row_id in data_row_ids:
        fields = [f for f in mdo.bulk_export([data_row_id])[0].fields]
        assert len(fields) == 1, fields
        assert SPLIT_SCHEMA_ID not in [field.schema_id for field in fields]


def test_bulk_delete_datarow_enum_metadata(datarow: DataRow, mdo):
    """test bulk deletes for non non fields"""
    metadata = make_metadata(datarow.uid)
    metadata.fields = [
        m for m in metadata.fields if m.schema_id == SPLIT_SCHEMA_ID
    ]
    mdo.bulk_upsert([metadata])

    exported = mdo.bulk_export([datarow.uid])[0].fields
    assert len(exported) == len(
        set([x.schema_id for x in metadata.fields] +
            [x.schema_id for x in exported]))

    mdo.bulk_delete([
        DeleteDataRowMetadata(data_row_id=datarow.uid, fields=[SPLIT_SCHEMA_ID])
    ])
    exported = mdo.bulk_export([datarow.uid])[0].fields
    assert len(exported) == 0


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
                                       schema_id=INVALID_SCHEMA_ID,
                                       value="message"),
                               ])
    with pytest.raises(ValueError):
        mdo.bulk_upsert([metadata])


def test_delete_non_existent_schema_id(datarow, mdo):
    res = mdo.bulk_delete([
        DeleteDataRowMetadata(data_row_id=datarow.uid, fields=[SPLIT_SCHEMA_ID])
    ])
    assert len(res) == 0


def test_parse_raw_metadata(mdo):
    example = {
        'dataRowId':
            'ckr6kkfx801ui0yrtg9fje8xh',
        'fields': [
            {
                'schemaId': 'cko8s9r5v0001h2dk9elqdidh',
                'value': 'my-new-message'
            },
            {
                'schemaId': 'cko8sbczn0002h2dkdaxb5kal',
                'value': {}
            },
            {
                'schemaId': 'cko8sbscr0003h2dk04w86hof',
                'value': {}
            },
            {
                'schemaId': 'cko8sdzv70006h2dk8jg64zvb',
                'value': '2021-07-20T21:41:14.606710Z'
            },
            {
                'schemaId': FAKE_SCHEMA_ID,
                'value': 0.5
            },
        ]
    }

    parsed = mdo.parse_metadata([example])
    assert len(parsed) == 1
    for row in parsed:
        assert row.data_row_id == example["dataRowId"]
        assert len(row.fields) == 4

    for row in parsed:
        for field in row.fields:
            assert mdo._parse_upsert(field)


def test_parse_raw_metadata_fields(mdo):
    example = [
        {
            'schemaId': 'cko8s9r5v0001h2dk9elqdidh',
            'value': 'my-new-message'
        },
        {
            'schemaId': 'cko8sbczn0002h2dkdaxb5kal',
            'value': {}
        },
        {
            'schemaId': 'cko8sbscr0003h2dk04w86hof',
            'value': {}
        },
        {
            'schemaId': 'cko8sdzv70006h2dk8jg64zvb',
            'value': '2021-07-20T21:41:14.606710Z'
        },
        {
            'schemaId': FAKE_SCHEMA_ID,
            'value': 0.5
        },
    ]

    parsed = mdo.parse_metadata_fields(example)
    assert len(parsed) == 4

    for field in parsed:
        assert mdo._parse_upsert(field)


def test_parse_metadata_schema():
    unparsed = {
        'id':
            'cl467a4ec0046076g7s9yheoa',
        'name':
            'enum metadata',
        'kind':
            'CustomMetadataEnum',
        'options': [{
            'id': 'cl467a4ec0047076ggjneeruy',
            'name': 'option1',
            'kind': 'CustomMetadataEnumOption'
        }, {
            'id': 'cl4qa31u0009e078p5m280jer',
            'name': 'option2',
            'kind': 'CustomMetadataEnumOption'
        }]
    }
    parsed = _parse_metadata_schema(unparsed)
    assert parsed.uid == 'cl467a4ec0046076g7s9yheoa'
    assert parsed.name == 'enum metadata'
    assert parsed.kind == DataRowMetadataKind.enum
    assert len(parsed.options) == 2
    assert parsed.options[0].uid == 'cl467a4ec0047076ggjneeruy'
    assert parsed.options[0].kind == DataRowMetadataKind.option


def test_create_schema(mdo):
    metadata_name = str(uuid.uuid4())
    created_schema = mdo.create_schema(metadata_name, DataRowMetadataKind.enum,
                                       ["option 1", "option 2"])
    assert created_schema.name == metadata_name
    assert created_schema.kind == DataRowMetadataKind.enum
    assert len(created_schema.options) == 2
    assert created_schema.options[0].name == "option 1"
    mdo.delete_schema(metadata_name)


def test_update_schema(mdo):
    metadata_name = str(uuid.uuid4())
    created_schema = mdo.create_schema(metadata_name, DataRowMetadataKind.enum,
                                       ["option 1", "option 2"])
    updated_schema = mdo.update_schema(metadata_name,
                                       f"{metadata_name}_updated")
    assert updated_schema.name == f"{metadata_name}_updated"
    assert updated_schema.uid == created_schema.uid
    assert updated_schema.kind == DataRowMetadataKind.enum
    mdo.delete_schema(f"{metadata_name}_updated")


def test_update_enum_options(mdo):
    metadata_name = str(uuid.uuid4())
    created_schema = mdo.create_schema(metadata_name, DataRowMetadataKind.enum,
                                       ["option 1", "option 2"])
    updated_schema = mdo.update_enum_option(metadata_name, "option 1",
                                            "option 3")
    assert updated_schema.name == metadata_name
    assert updated_schema.uid == created_schema.uid
    assert updated_schema.kind == DataRowMetadataKind.enum
    assert updated_schema.options[0].uid == created_schema.options[0].uid
    assert updated_schema.options[0].name == "option 3"
    mdo.delete_schema(metadata_name)


def test_delete_schema(mdo):
    metadata_name = str(uuid.uuid4())
    created_schema = mdo.create_schema(metadata_name,
                                       DataRowMetadataKind.string)
    status = mdo.delete_schema(created_schema.name)
    mdo.refresh_ontology()
    assert status
    assert metadata_name not in mdo.custom_by_name


@pytest.mark.parametrize('datetime_str',
                         ['2011-11-04T00:05:23Z', '2011-05-07T14:34:14+00:00'])
def test_upsert_datarow_date_metadata(datarow, mdo, datetime_str):
    metadata = [
        DataRowMetadata(data_row_id=datarow.uid,
                        fields=[
                            DataRowMetadataField(name='captureDateTime',
                                                 value=datetime_str),
                        ])
    ]
    errors = mdo.bulk_upsert(metadata)
    assert len(errors) == 0

    metadata = mdo.bulk_export([datarow.uid])
    assert metadata[0].fields[0].value == datetime.fromisoformat(datetime_str)


@pytest.mark.parametrize('datetime_str',
                         ['2011-11-04T00:05:23Z', '2011-05-07T14:34:14+00:00'])
def test_create_data_row_with_metadata(dataset, image_url, datetime_str):
    client = dataset.client
    assert len(list(dataset.data_rows())) == 0

    metadata_fields = [
        DataRowMetadataField(name='captureDateTime', value=datetime_str)
    ]

    data_row = dataset.create_data_row(row_data=image_url,
                                       metadata_fields=metadata_fields)

    retrieved_data_row = client.get_data_row(data_row.uid)
    assert retrieved_data_row.metadata[0].value == datetime.fromisoformat(
        datetime_str)
