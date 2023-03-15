from typing import Dict, Any

from pydantic import BaseModel, root_validator


class TextEntity(BaseModel):
    """ Represents a text entity """
    start: int
    end: int
    extra: Dict[str, Any] = {}

    @root_validator
    def validate_start_end(cls, values):
        if 'start' in values and 'end' in values:
            if (isinstance(values['start'], int) and
                    values['start'] > values['end']):
                raise ValueError(
                    "Location end must be greater or equal to start")
        return values
