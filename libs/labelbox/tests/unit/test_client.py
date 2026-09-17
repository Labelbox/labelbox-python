from ipaddress import ip_address, ip_network
from unittest.mock import Mock, patch

import pytest
from lbox.exceptions import ResourceNotFoundError

from labelbox.client import Client
from labelbox.schema.api_key import ApiKey
from labelbox.schema.embedding import Embedding
from labelbox.schema.timeunit import TimeUnit


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


def test_create_api_key_forwards_ip_allowlist():
    client = Client(api_key="api_key")
    allowed_ip_cidrs = [
        ip_address("203.0.113.10"),
        ip_network("198.51.100.0/24"),
    ]
    with patch.object(
        ApiKey,
        "create_api_key",
        return_value={"id": "key-1", "jwt": "secret"},
    ) as create_api_key:
        with pytest.warns(UserWarning, match="currently in alpha"):
            result = client.create_api_key(
                name="Restricted key",
                user="person@example.com",
                role="Admin",
                validity=5,
                time_unit=TimeUnit.MINUTE,
                allowed_ip_cidrs=allowed_ip_cidrs,
            )

        create_api_key.assert_called_once_with(
            client,
            "Restricted key",
            "person@example.com",
            "Admin",
            5,
            TimeUnit.MINUTE,
            allowed_ip_cidrs,
        )

    assert result == {"id": "key-1", "jwt": "secret"}
