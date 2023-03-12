from typing import List

from pydantic import BaseModel, validator


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
    textSelections: List[DocumentTextSelection]
