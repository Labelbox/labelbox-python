from typing import Optional

from pydantic import BaseModel


class ConfidenceMixin(BaseModel):
    confidence: Optional[float] = None
