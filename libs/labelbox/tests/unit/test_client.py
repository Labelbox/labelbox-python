from unittest.mock import Mock

import pytest
from lbox.exceptions import ResourceNotFoundError

from labelbox.client import Client
from labelbox.schema.embedding import Embedding


# @patch.dict(os.environ, {'LABELBOX_API_KEY': 'bar'})
def test_headers():
    client = Client(api_key="api_key", endpoint="http://localhost:8080/_gql")
    assert client.headers
    assert client.headers["Authorization"] == "Bearer api_key"
    assert client.headers["Content-Type"] == "application/json"
    assert client.headers["User-Agent"]
    assert client.headers["X-Python-Version"]


def test_enable_experimental():
    client = Client(api_key="api_key", enable_experimental=True)
    assert client.enable_experimental


def test_create_embedding_uses_graphql():
    client = Client(api_key="api_key")
    client.execute = Mock(
        return_value={
            "createEmbedding": {
                "id": "embedding-id",
                "name": "custom",
                "dims": 8,
                "custom": True,
            }
        }
    )

    embedding = client.create_embedding("custom", 8)

    assert embedding.id == "embedding-id"
    query, variables = client.execute.call_args.args
    assert "createEmbedding" in query
    assert variables == {"data": {"name": "custom", "dims": 8}}


def test_get_embeddings_uses_graphql():
    client = Client(api_key="api_key")
    client.execute = Mock(
        return_value={
            "embeddings": [
                {
                    "id": "embedding-id",
                    "name": "custom",
                    "dims": 8,
                    "custom": True,
                }
            ]
        }
    )

    embeddings = client.get_embeddings()

    assert [embedding.id for embedding in embeddings] == ["embedding-id"]
    assert "embeddings" in client.execute.call_args.args[0]


def test_get_embedding_by_id_filters_graphql_results():
    client = Client(api_key="api_key")
    client.get_embeddings = Mock(
        return_value=[
            Embedding(
                client,
                id="embedding-id",
                name="custom",
                dims=8,
                custom=True,
            )
        ]
    )

    assert client.get_embedding_by_id("embedding-id").name == "custom"

    with pytest.raises(ResourceNotFoundError):
        client.get_embedding_by_id("missing")


def test_embedding_delete_uses_graphql():
    client = Client(api_key="api_key")
    client.execute = Mock(return_value={"deleteEmbedding": True})
    embedding = Embedding(
        client,
        id="embedding-id",
        name="custom",
        dims=8,
        custom=True,
    )

    embedding.delete()

    query, variables = client.execute.call_args.args
    assert "deleteEmbedding" in query
    assert variables == {"data": {"id": "embedding-id"}}


def test_embedding_vector_operations_remain_on_adv():
    client = Client(api_key="api_key")
    client._adv_client.import_vectors_from_file = Mock()
    client._adv_client.get_imported_vector_count = Mock(return_value=12)
    callback = Mock()
    embedding = Embedding(
        client,
        id="embedding-id",
        name="custom",
        dims=8,
        custom=True,
    )

    embedding.import_vectors_from_file("vectors.ndjson", callback)

    client._adv_client.import_vectors_from_file.assert_called_once_with(
        "embedding-id", "vectors.ndjson", callback
    )
    assert embedding.get_imported_vector_count() == 12
