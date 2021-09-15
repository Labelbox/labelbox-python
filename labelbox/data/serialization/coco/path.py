from pydantic import BaseModel
from pathlib import Path


class PathSerializerMixin(BaseModel):

    def dict(self, *args, **kwargs):
        res = super().dict(*args, **kwargs)
        return {k: str(v) if isinstance(v, Path) else v for k, v in res.items()}
