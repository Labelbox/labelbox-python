from typing import List

from pydantic import BaseModel, validator

from labelbox.utils import _CamelCaseMixin


class DocumentTextSelection(_CamelCaseMixin, BaseModel):
    token_ids: List[str]
    group_id: str
    page: int

    @validator("page")
    def validate_page(cls, v):
        if v < 1:
            raise ValueError("Page must be greater than 1")
        return v


class DocumentEntity(_CamelCaseMixin, BaseModel):
    """ Represents a text entity """
    text_selections: List[DocumentTextSelection]
