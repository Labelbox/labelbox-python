from typing import List

from labelbox import pydantic_compat
from labelbox.utils import _CamelCaseMixin


class DocumentTextSelection(_CamelCaseMixin, pydantic_compat.BaseModel):
    token_ids: List[str]
    group_id: str
    page: int

    @pydantic_compat.validator("page")
    def validate_page(cls, v):
        if v < 1:
            raise ValueError("Page must be greater than 1")
        return v


class DocumentEntity(_CamelCaseMixin, pydantic_compat.BaseModel):
    """ Represents a text entity """
    text_selections: List[DocumentTextSelection]
