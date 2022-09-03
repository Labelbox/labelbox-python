from pydantic import BaseModel

from labelbox.utils import camel_case


class _CamelCaseMixin(BaseModel):

    class Config:
        allow_population_by_field_name = True
        alias_generator = camel_case


class AssignGlobalKeyToDataRowInput(_CamelCaseMixin):
    data_row_id: str
    global_key: str
