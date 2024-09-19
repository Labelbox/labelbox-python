from typing import Optional

from pydantic import BaseModel, model_validator


class DataRow(BaseModel):
    """Generic data row data. This is replacing all other DataType passed into Label"""

    id: str
    url: Optional[str] = None
    global_key: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def validate_one_datarow_key_present(cls, data):
        keys = ["global_key", "id"]
        count = sum([key in data for key in keys])

        if count < 1:
            raise ValueError(f"Exactly one of {keys} must be present.")
        if count > 1:
            raise ValueError(f"Only one of {keys} can be present.")
        return data
