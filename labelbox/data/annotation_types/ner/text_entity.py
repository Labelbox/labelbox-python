from typing import Dict, Any

from labelbox import pydantic_compat


class TextEntity(pydantic_compat.BaseModel):
    """ Represents a text entity """
    start: int
    end: int
    extra: Dict[str, Any] = {}

    @pydantic_compat.root_validator
    def validate_start_end(cls, values):
        if 'start' in values and 'end' in values:
            if (isinstance(values['start'], int) and
                    values['start'] > values['end']):
                raise ValueError(
                    "Location end must be greater or equal to start")
        return values
