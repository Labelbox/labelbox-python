from typing import Dict, Any, List

from pydantic import BaseModel, root_validator, validator


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


class DocumentTextSelection(BaseModel):
    tokenIds: List[str]
    groupId: str
    page: int

    @validator("page")
    def validate_page(cls, v):
        if v < 1:
            raise ValueError("Page must be greater than 1")
        return v

class DocumentEntity(BaseModel):
    """ Represents a text entity """
    name: str
    text_selections: List[DocumentTextSelection]
