from labelbox.utils import _CamelCaseMixin

from pydantic import BaseModel

from datetime import datetime
from typing import Dict


class Model(_CamelCaseMixin, BaseModel):
    id: str
    description: str
    inference_params_json_schema: Dict
    name: str
    ontology_id: str
    created_at: datetime


MODEL_FIELD_NAMES = list(Model.schema()['properties'].keys())
