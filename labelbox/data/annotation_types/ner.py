from typing import Dict, Any

from pydantic import BaseModel, root_validator, ValidationError


class TextEntity(BaseModel):
    start: int
    end: int
    extras: Dict[str, Any] = {}

    @root_validator
    def validate_start_end(cls, values):
        if (isinstance(values['start'], int) and
                values['start'] >= values['end']):
            raise ValidationError(
                "Location end must be greater or equal to start")
        return values
