from labelbox.utils import _CamelCaseMixin


from datetime import datetime
from typing import Dict
from pydantic import BaseModel


class Model(_CamelCaseMixin, BaseModel):
    id: str
    description: str
    inference_params_json_schema: Dict
    name: str
    ontology_id: str
    created_at: datetime


MODEL_FIELD_NAMES = list(Model.model_json_schema()["properties"].keys())
