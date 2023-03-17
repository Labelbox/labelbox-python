from typing import List, Optional
from uuid import uuid4
from pydantic import root_validator, validator

from labelbox.data.serialization.ndjson.base import NDJsonBase
from .data_row import DataRow
from labelbox.data.serialization.ndjson.types import NDSubclassificationType
from labelbox.utils import _CamelCaseMixin

from ...annotation_types.types import Cuid


class NDAnnotation(NDJsonBase):
    name: Optional[str] = None
    classifications: List[NDSubclassificationType] = []
    schema_id: Optional[Cuid] = None
    page: Optional[int] = None
    unit: Optional[str] = None

    @root_validator()
    def must_set_one(cls, values):
        if ('schema_id' not in values or
                values['schema_id'] is None) and ('name' not in values or
                                                  values['name'] is None):
            raise ValueError("Schema id or name are not set. Set either one.")
        return values

    def dict(self, *args, **kwargs):
        res = super().dict(*args, **kwargs)
        if 'name' in res and res['name'] is None:
            res.pop('name')
        if 'schemaId' in res and res['schemaId'] is None:
            res.pop('schemaId')
        return res
