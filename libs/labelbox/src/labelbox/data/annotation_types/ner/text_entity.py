from typing import Dict, Any

from pydantic import BaseModel, model_validator


class TextEntity(BaseModel):
    """Represents a text entity"""

    start: int
    end: int
    extra: Dict[str, Any] = {}

    @model_validator(mode="after")
    def validate_start_end(self, values):
        if hasattr(self, "start") and hasattr(self, "end"):
            if isinstance(self.start, int) and self.start > self.end:
                raise ValueError(
                    "Location end must be greater or equal to start"
                )
        return self
