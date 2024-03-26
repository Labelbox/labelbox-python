from typing import List, Optional, Any, Dict

from labelbox.pydantic_compat import BaseModel


class EmbeddingVector(BaseModel):
    embedding_id: str
    vector: List[float]
    clusters: Optional[List[int]]

    def to_gql(self) -> Dict[str, Any]:
        result = {"embeddingId": self.embedding_id, "vector": self.vector}
        if self.clusters:
            result["clusters"] = self.clusters
        return result
