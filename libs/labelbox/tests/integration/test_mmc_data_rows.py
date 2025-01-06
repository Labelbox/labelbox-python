import json
import random

import pytest

from labelbox.schema.data_row_payload_templates import ModelEvaluationTemplate


@pytest.fixture
def mmc_data_row(dataset):
    data = ModelEvaluationTemplate()

    content_all = data.model_dump(exclude_none=True)
    task = dataset.create_data_rows([content_all])
    task.wait_till_done()
    assert task.status == "COMPLETE"

    data_row = list(dataset.data_rows())[0]

    yield data_row

    data_row.delete()


@pytest.fixture
def mmc_data_row_all(dataset, make_metadata_fields, embedding, rand_gen):
    data = ModelEvaluationTemplate()
    data.row_data.rootMessageIds = ["root1"]
    global_key = f"global_key_{rand_gen(str)}"
    data.global_key = global_key
    vector = [random.uniform(1.0, 2.0) for _ in range(embedding.dims)]
    data.embeddings = [{"embedding_id": embedding.id, "vector": vector}]
    data.metadata_fields = make_metadata_fields
    data.attachments = [{"type": "RAW_TEXT", "value": "attachment value"}]

    content_all = data.model_dump(exclude_none=True)
    task = dataset.create_data_rows([content_all])
    task.wait_till_done()
    assert task.status == "COMPLETE"

    data_row = list(dataset.data_rows())[0]

    yield data_row, global_key

    data_row.delete()


def test_mmc(mmc_data_row):
    data_row = mmc_data_row
    assert json.loads(data_row.row_data) == {
        "type": "application/vnd.labelbox.conversational.model-chat-evaluation",
        "draft": True,
        "rootMessageIds": [],
        "actors": {},
        "messages": {},
        "version": 2,
    }


def test_mmc_all(mmc_data_row_all, embedding, constants):
    data_row, global_key = mmc_data_row_all
    assert json.loads(data_row.row_data) == {
        "type": "application/vnd.labelbox.conversational.model-chat-evaluation",
        "draft": True,
        "rootMessageIds": ["root1"],
        "actors": {},
        "messages": {},
        "version": 2,
    }
    assert data_row.global_key == global_key
    metadata_fields = data_row.metadata_fields
    metadata = data_row.metadata
    assert len(metadata_fields) == 3
    assert len(metadata) == 3
    assert [m["schemaId"] for m in metadata_fields].sort() == constants[
        "EXPECTED_METADATA_SCHEMA_IDS"
    ].sort()

    attachments = list(data_row.attachments())
    assert len(attachments) == 1

    assert embedding.get_imported_vector_count() == 1
