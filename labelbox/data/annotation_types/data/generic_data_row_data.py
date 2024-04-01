from typing import Callable, Literal, Optional

from labelbox import pydantic_compat
from labelbox.data.annotation_types.data.base_data import BaseData
from labelbox.utils import _NoCoercionMixin


class GenericDataRowData(BaseData, _NoCoercionMixin):
    """Generic data row data
    """
    url: Optional[str] = None
    class_name: Literal["GenericDataRowData"] = "GenericDataRowData"

    def create_url(self, signer: Callable[[bytes], str]) -> None:
        return None

    @pydantic_compat.root_validator(pre=True)
    def validate_one_datarow_key_present(cls, data):
        keys = ['external_id', 'global_key', 'uid']
        count = 0
        for key in keys:
            if data.get(key):
                count += 1
        if count < 1:
            raise ValueError(f"Exactly one of {keys} must be present.")
        if count > 1:
            raise ValueError(f"Only one of {keys} can be present.")
        return data
