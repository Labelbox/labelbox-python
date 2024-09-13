import json
import random
import threading
from tempfile import NamedTemporaryFile
from typing import List, Dict, Any

import pytest

import labelbox.exceptions
from labelbox import Client, Dataset, DataRow
from labelbox.schema.embedding import Embedding


def test_get_embedding_by_id(client: Client, embedding: Embedding):
    e = client.get_embedding_by_id(embedding.id)
    assert e.id == embedding.id

    e = client.get_embedding_by_name(embedding.name)
    assert e.name == embedding.name

    embeddings = client.get_embeddings()
    assert len(embeddings) > 0


def test_get_embedding_by_name_not_found(client: Client):
    with pytest.raises(labelbox.exceptions.ResourceNotFoundError):
        client.get_embedding_by_name("does-not-exist")


@pytest.mark.parametrize("data_rows", [10], indirect=True)
def test_import_vectors_from_file(
    data_rows: List[DataRow], embedding: Embedding
):
    vector = [random.uniform(1.0, 2.0) for _ in range(embedding.dims)]
    event = threading.Event()

    def callback(_: Dict[str, Any]):
        event.set()

    with NamedTemporaryFile(mode="w+") as fp:
        lines = [
            json.dumps({"id": dr.uid, "vector": vector}) for dr in data_rows
        ]
        fp.writelines(lines)
        fp.flush()
        embedding.import_vectors_from_file(fp.name, callback)

    assert event.wait(10.0)  # seconds


def test_get_imported_vector_count(dataset: Dataset, embedding: Embedding):
    assert embedding.get_imported_vector_count() == 0

    vector = [random.uniform(1.0, 2.0) for _ in range(embedding.dims)]
    dataset.create_data_row(
        row_data="foo",
        embeddings=[{"embedding_id": embedding.id, "vector": vector}],
    )

    assert embedding.get_imported_vector_count() == 1
