import json
import random
import threading
import uuid
from tempfile import NamedTemporaryFile
from typing import List, Dict, Any

import pytest

from labelbox import Client, Dataset, DataRow
from labelbox.schema.embedding import Embedding


@pytest.fixture
def embedding(client: Client):
    uuid_str = uuid.uuid4().hex
    embedding = client.create_embedding(f"sdk-int-{uuid_str}", 8)
    yield embedding
    embedding.delete()


def test_get_embedding(client: Client, embedding: Embedding):
    e = client.get_embedding(embedding.id)
    assert e.id == embedding.id


def test_get_embeddings(client: Client, embedding: Embedding):
    embeddings = client.get_embeddings()
    assert len(embeddings) > 0


@pytest.mark.parametrize('data_rows', [10], indirect=True)
def test_import_vectors_from_file(data_rows: List[DataRow],
                                  embedding: Embedding):
    vector = [random.uniform(1.0, 2.0) for _ in range(8)]
    event = threading.Event()

    def callback(_: Dict[str, Any]):
        event.set()

    with NamedTemporaryFile(mode="w+") as fp:
        lines = [
            json.dumps({
                "id": dr.uid,
                "vector": vector
            }) for dr in data_rows
        ]
        fp.writelines(lines)
        fp.flush()
        embedding.import_vectors_from_file(fp.name, callback)

    assert event.wait(10.0)  # seconds


def test_get_imported_vector_count(dataset: Dataset, embedding: Embedding):
    assert embedding.get_imported_vector_count() == 0

    vector = [random.uniform(1.0, 2.0) for _ in range(8)]
    dataset.create_data_row(row_data="foo",
                            embeddings=[{
                                "embedding_id": embedding.id,
                                "vector": vector
                            }])

    assert embedding.get_imported_vector_count() == 1
