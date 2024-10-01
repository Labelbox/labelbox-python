import json
import random

import pytest


@pytest.fixture
def mmc_data_row(dataset, make_metadata_fields, embedding):
    row_data = {
        "type": "application/vnd.labelbox.conversational.model-chat-evaluation",
        "draft": True,
        "rootMessageIds": ["root1"],
        "actors": {},
        "messages": {},
    }

    vector = [random.uniform(1.0, 2.0) for _ in range(embedding.dims)]
    embeddings = [{"embedding_id": embedding.id, "vector": vector}]

    content_all = {
        "row_data": row_data,
        "attachments": [{"type": "RAW_TEXT", "value": "attachment value"}],
        "metadata_fields": make_metadata_fields,
        "embeddings": embeddings,
    }
    task = dataset.create_data_rows([content_all])
    task.wait_till_done()
    assert task.status == "COMPLETE"

    data_row = list(dataset.data_rows())[0]

    yield data_row

    data_row.delete()


def test_mmc(mmc_data_row, embedding, constants):
    data_row = mmc_data_row
    assert json.loads(data_row.row_data) == {
        "type": "application/vnd.labelbox.conversational.model-chat-evaluation",
        "draft": True,
        "rootMessageIds": ["root1"],
        "actors": {},
        "messages": {},
    }

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
