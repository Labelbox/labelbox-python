from pathlib import Path
from pydantic import BaseModel, model_serializer


class PathSerializerMixin(BaseModel):
    @model_serializer(mode="wrap")
    def serialize_model(self, handler):
        res = handler(self)
        return {k: str(v) if isinstance(v, Path) else v for k, v in res.items()}
