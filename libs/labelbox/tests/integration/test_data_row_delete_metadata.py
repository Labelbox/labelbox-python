from datetime import datetime, timezone
import uuid

import pytest

from labelbox import DataRow, Dataset, Client, DataRowMetadataOntology
from labelbox.exceptions import MalformedQueryException
from labelbox.schema.data_row_metadata import (
    DataRowMetadataField,
    DataRowMetadata,
    DataRowMetadataKind,
    DeleteDataRowMetadata,
)
from labelbox.schema.identifiable import GlobalKey, UniqueId

INVALID_SCHEMA_ID = "1" * 25
FAKE_SCHEMA_ID = "0" * 25
FAKE_DATAROW_ID = "D" * 25
SPLIT_SCHEMA_ID = "cko8sbczn0002h2dkdaxb5kal"
TRAIN_SPLIT_ID = "cko8sbscr0003h2dk04w86hof"
TEST_SPLIT_ID = "cko8scbz70005h2dkastwhgqt"
TEXT_SCHEMA_ID = "cko8s9r5v0001h2dk9elqdidh"
CAPTURE_DT_SCHEMA_ID = "cko8sdzv70006h2dk8jg64zvb"
CUSTOM_TEXT_SCHEMA_NAME = "custom_text"

FAKE_NUMBER_FIELD = {
    "id": FAKE_SCHEMA_ID,
    "name": "number",
    "kind": "CustomMetadataNumber",
    "reserved": False,
}


@pytest.fixture
def mdo(client: Client):
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
    task = dataset.create_data_rows(
        [
            {
                "row_data": image_url,
                "external_id": "my-image",
                "global_key": str(uuid.uuid4()),
            },
        ]
        * 5
    )
    task.wait_till_done()

    yield dataset


def make_metadata(dr_id: str = None, gk: str = None) -> DataRowMetadata:
    msg = "A message"
    time = datetime.now(timezone.utc)

    metadata = DataRowMetadata(
        global_key=gk,
        data_row_id=dr_id,
        fields=[
            DataRowMetadataField(
                schema_id=SPLIT_SCHEMA_ID, value=TEST_SPLIT_ID
            ),
            DataRowMetadataField(schema_id=CAPTURE_DT_SCHEMA_ID, value=time),
            DataRowMetadataField(schema_id=TEXT_SCHEMA_ID, value=msg),
        ],
    )
    return metadata


def make_named_metadata(dr_id) -> DataRowMetadata:
    msg = "A message"
    time = datetime.now(timezone.utc)

    metadata = DataRowMetadata(
        data_row_id=dr_id,
        fields=[
            DataRowMetadataField(name="split", value=TEST_SPLIT_ID),
            DataRowMetadataField(name="captureDateTime", value=time),
            DataRowMetadataField(name=CUSTOM_TEXT_SCHEMA_NAME, value=msg),
        ],
    )
    return metadata


@pytest.mark.order(1)
def test_bulk_delete_datarow_metadata(data_row, mdo):
    """test bulk deletes for all fields"""
    metadata = make_metadata(data_row.uid)
    mdo.bulk_upsert([metadata])
    assert len(mdo.bulk_export([data_row.uid])[0].fields)
    upload_ids = [m.schema_id for m in metadata.fields[:-2]]
    mdo.bulk_delete(
        [DeleteDataRowMetadata(data_row_id=data_row.uid, fields=upload_ids)]
    )
    remaining_ids = set(
        [f.schema_id for f in mdo.bulk_export([data_row.uid])[0].fields]
    )
    assert not len(remaining_ids.intersection(set(upload_ids)))


@pytest.fixture
def data_row_unique_id(data_row):
    return UniqueId(data_row.uid)


@pytest.fixture
def data_row_global_key(data_row):
    return GlobalKey(data_row.global_key)


@pytest.fixture
def data_row_id_as_str(data_row):
    return data_row.uid


@pytest.mark.parametrize(
    "data_row_for_delete",
    ["data_row_id_as_str", "data_row_unique_id", "data_row_global_key"],
)
def test_bulk_delete_datarow_metadata(
    data_row_for_delete, data_row, mdo, request
):
    """test bulk deletes for all fields"""
    metadata = make_metadata(data_row.uid)
    mdo.bulk_upsert([metadata])
    assert len(mdo.bulk_export([data_row.uid])[0].fields)
    upload_ids = [m.schema_id for m in metadata.fields[:-2]]
    mdo.bulk_delete(
        [
            DeleteDataRowMetadata(
                data_row_id=request.getfixturevalue(data_row_for_delete),
                fields=upload_ids,
            )
        ]
    )
    remaining_ids = set(
        [f.schema_id for f in mdo.bulk_export([data_row.uid])[0].fields]
    )
    assert not len(remaining_ids.intersection(set(upload_ids)))


@pytest.mark.parametrize(
    "data_row_for_delete",
    ["data_row_id_as_str", "data_row_unique_id", "data_row_global_key"],
)
def test_bulk_partial_delete_datarow_metadata(
    data_row_for_delete, data_row, mdo, request
):
    """Delete a single from metadata"""
    n_fields = len(mdo.bulk_export([data_row.uid])[0].fields)
    metadata = make_metadata(data_row.uid)
    mdo.bulk_upsert([metadata])

    assert len(mdo.bulk_export([data_row.uid])[0].fields) == (
        n_fields + len(metadata.fields)
    )

    mdo.bulk_delete(
        [
            DeleteDataRowMetadata(
                data_row_id=request.getfixturevalue(data_row_for_delete),
                fields=[TEXT_SCHEMA_ID],
            )
        ]
    )
    fields = [f for f in mdo.bulk_export([data_row.uid])[0].fields]
    assert len(fields) == (len(metadata.fields) - 1)


@pytest.fixture
def data_row_unique_ids(big_dataset):
    deletes = []
    data_row_ids = [dr.uid for dr in big_dataset.data_rows()]

    for data_row_id in data_row_ids:
        deletes.append(
            DeleteDataRowMetadata(
                data_row_id=UniqueId(data_row_id),
                fields=[SPLIT_SCHEMA_ID, CAPTURE_DT_SCHEMA_ID],
            )
        )
    return deletes


@pytest.fixture
def data_row_ids_as_str(big_dataset):
    deletes = []
    data_row_ids = [dr.uid for dr in big_dataset.data_rows()]

    for data_row_id in data_row_ids:
        deletes.append(
            DeleteDataRowMetadata(
                data_row_id=data_row_id,
                fields=[SPLIT_SCHEMA_ID, CAPTURE_DT_SCHEMA_ID],
            )
        )
    return deletes


@pytest.fixture
def data_row_global_keys(big_dataset):
    deletes = []
    global_keys = [dr.global_key for dr in big_dataset.data_rows()]

    for data_row_id in global_keys:
        deletes.append(
            DeleteDataRowMetadata(
                data_row_id=GlobalKey(data_row_id),
                fields=[SPLIT_SCHEMA_ID, CAPTURE_DT_SCHEMA_ID],
            )
        )
    return deletes


@pytest.mark.parametrize(
    "data_rows_for_delete",
    ["data_row_ids_as_str", "data_row_unique_ids", "data_row_global_keys"],
)
def test_large_bulk_delete_datarow_metadata(
    data_rows_for_delete, big_dataset, mdo, request
):
    metadata = []
    data_row_ids = [dr.uid for dr in big_dataset.data_rows()]
    for data_row_id in data_row_ids:
        metadata.append(
            DataRowMetadata(
                data_row_id=data_row_id,
                fields=[
                    DataRowMetadataField(
                        schema_id=SPLIT_SCHEMA_ID, value=TEST_SPLIT_ID
                    ),
                    DataRowMetadataField(
                        schema_id=TEXT_SCHEMA_ID, value="test-message"
                    ),
                ],
            )
        )
    errors = mdo.bulk_upsert(metadata)
    assert len(errors) == 0

    deletes = request.getfixturevalue(data_rows_for_delete)
    errors = mdo.bulk_delete(deletes)

    assert len(errors) == len(data_row_ids)
    for error in errors:
        assert error.fields == [CAPTURE_DT_SCHEMA_ID]
        assert error.error == "Schema did not exist"

    for data_row_id in data_row_ids:
        fields = [f for f in mdo.bulk_export([data_row_id])[0].fields]
        assert len(fields) == 1, fields
        assert SPLIT_SCHEMA_ID not in [field.schema_id for field in fields]


@pytest.mark.parametrize(
    "data_row_for_delete",
    ["data_row_id_as_str", "data_row_unique_id", "data_row_global_key"],
)
def test_bulk_delete_datarow_enum_metadata(
    data_row_for_delete,
    data_row: DataRow,
    mdo: DataRowMetadataOntology,
    request,
):
    """test bulk deletes for non non fields"""
    metadata = make_metadata(data_row.uid)
    metadata.fields = [
        m for m in metadata.fields if m.schema_id == SPLIT_SCHEMA_ID
    ]
    mdo.bulk_upsert([metadata])

    exported = mdo.bulk_export([data_row.uid])[0].fields
    assert len(exported) == len(
        set(
            [x.schema_id for x in metadata.fields]
            + [x.schema_id for x in exported]
        )
    )

    mdo.bulk_delete(
        [
            DeleteDataRowMetadata(
                data_row_id=request.getfixturevalue(data_row_for_delete),
                fields=[SPLIT_SCHEMA_ID],
            )
        ]
    )
    exported = mdo.bulk_export([data_row.uid])[0].fields
    assert len(exported) == 0


@pytest.mark.parametrize(
    "data_row_for_delete",
    ["data_row_id_as_str", "data_row_unique_id", "data_row_global_key"],
)
def test_delete_non_existent_schema_id(
    data_row_for_delete, data_row, mdo, request
):
    res = mdo.bulk_delete(
        [
            DeleteDataRowMetadata(
                data_row_id=request.getfixturevalue(data_row_for_delete),
                fields=[SPLIT_SCHEMA_ID],
            )
        ]
    )
    assert len(res) == 1
    assert res[0].fields == [SPLIT_SCHEMA_ID]
    assert res[0].error == "Schema did not exist"
