from typing import Optional, Callable, Dict, Any, List

from labelbox.adv_client import AdvClient
from pydantic import BaseModel, PrivateAttr


class EmbeddingVector(BaseModel):
    """
    A Vector Embedding for Custom Embedding.

    Attributes:
        embedding_id (str): The ID of the associated Embedding
        vector (list): The raw vector values - the number of entries should match the Embedding's dimensions
        clusters (list): The cluster groupings
    """

    embedding_id: str
    vector: List[float]
    clusters: Optional[List[int]] = None

    def to_gql(self) -> Dict[str, Any]:
        result = {"embeddingId": self.embedding_id, "vector": self.vector}
        if self.clusters:
            result["clusters"] = self.clusters
        return result


class Embedding(BaseModel):
    """
    An Embedding is used to power similarity search in Catalog.

    This model supports the representation of both `Precomputed` embeddings that Labelbox provides,
    and `Custom` embeddings which can be imported directly into Labelbox.

    Attributes:
        id (str): The ID of the embedding
        name (str): The name of the embedding
        dims (int): Refers to the size of the vector space in which words, phrases, or other entities are embedded
        custom (bool): Indicates whether the embedding is a Precomputed embedding or a Custom embedding
    """

    id: str
    name: str
    custom: bool
    dims: int
    _client: AdvClient = PrivateAttr()

    def __init__(self, client: AdvClient, **data):
        super().__init__(**data)
        self._client = client

    def delete(self):
        """
        Delete a custom embedding.  If the embedding does not exist or
        cannot be deleted, an AdvLibException is raised.
        """
        self._client.delete_embedding(self.id)

    def import_vectors_from_file(
        self,
        path: str,
        callback: Optional[Callable[[Dict[str, Any]], None]] = None,
    ):
        """
        Import vectors into a given embedding from an NDJSON file.  An
        NDJSON file consists of newline delimited JSON.  Each line of the file
        is valid JSON, but the entire file itself is NOT.  The format of the
        file looks like:

            {"id": DATAROW ID1, "vector": [ array of floats ]}\n
            {"id": DATAROW ID2, "vector": [ array of floats ]}\n
            {"id": DATAROW ID3, "vector": [ array of floats ]}

        The vectors are added to the system in an async manner and it may take
        up to a couple minutes before they are usable via similarity search. Note
        that you also need to upload at least 1000 vectors in order for similarity
        search to be activated.

        Args:
            path: The path to the NDJSON file.
            callback: a callback function used get the status of each batch of lines uploaded.
        """
        self._client.import_vectors_from_file(self.id, path, callback)

    def get_imported_vector_count(self) -> int:
        """
        Return the # of vectors actually imported into Labelbox.  This will give you an accurate
        count of the number of vectors written into the vector search system.

        Returns:
            The number of imported vectors.
        """
        return self._client.get_imported_vector_count(self.id)

    @classmethod
    def type_name(cls):
        return cls.__name__.split(".")[-1]
