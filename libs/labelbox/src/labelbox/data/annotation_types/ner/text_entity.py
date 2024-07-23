from typing import Dict, Any

from pydantic import BaseModel, model_validator


class TextEntity(BaseModel):
    """ Represents a text entity """
    start: int
    end: int
    extra: Dict[str, Any] = {}

    @model_validator(mode="after")
    def validate_start_end(cls, values):
        if hasattr(cls, 'start') and hasattr(cls, 'end'):
            if (isinstance(cls.start, int) and
                    cls.start > cls.end):
                raise ValueError(
                    "Location end must be greater or equal to start")
        return cls
