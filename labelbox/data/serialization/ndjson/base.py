from uuid import uuid4
from pydantic import BaseModel, validator, Field


def to_camel(string: str) -> str:
    return ''.join(word.capitalize() for word in string.split('_'))


class DataRow(BaseModel):
    id: str = None

    @validator('id', pre=True, always=True)
    def validate_id(cls, v):
        if v is None:
            raise ValueError(
                "Data row ids are not set. Use `LabelGenerator.add_to_dataset`, `LabelCollection.add_to_dataset`, or `Label.create_data_row`. "
                "You can also manually assign the id for each `BaseData` object"
            )
        return v


class NDJsonBase(BaseModel):
    uuid: str = None
    data_row: DataRow = Field(..., alias="dataRow")

    @validator('uuid', pre=True, always=True)
    def set_id(cls, v):
        return v or str(uuid4())

    class Config:
        allow_population_by_field_name = True


class NDAnnotation(NDJsonBase):
    schema_id: str = Field(None, alias="schemaId")

    @validator('schema_id', pre=True, always=True)
    def validate_id(cls, v):
        if v is None:
            raise ValueError(
                "Schema ids are not set. Use `LabelGenerator.assign_schema_ids`, `LabelCollection.assign_schema_ids`, or `Label.assign_schema_ids`."
            )
        return v
