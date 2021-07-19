

from uuid import UUID, uuid4
from pydantic import BaseModel, validator


def to_camel(string: str) -> str:
    return ''.join(word.capitalize() for word in string.split('_'))


class DataRow(BaseModel):
    id: str
    # TODO: If datarow.id is None. Then we will throw a nice error asking users to use our upload to dataset function.

class NDJsonBase(BaseModel):
    uuid: str = None
    dataRow: DataRow

    @validator('uuid', pre=True, always=True)
    def set_id(cls, v):
        return v or str(uuid4())


    class Config:
        #alias_generator = to_camel
        allow_population_by_field_name = True


class NDAnnotation(NDJsonBase):
    schemaId: str
    # TODO: If schema.id is None. Then we will throw a nice error asking users to use our assign schema id function.


