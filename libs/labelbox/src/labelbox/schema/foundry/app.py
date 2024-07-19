from labelbox.utils import _CamelCaseMixin
from typing import Any, Dict, Optional
from pydantic import BaseModel


class App(_CamelCaseMixin, BaseModel):
    id: Optional[str]
    model_id: str
    name: str
    description: Optional[str] = None
    inference_params: Dict[str, Any]
    class_to_schema_id: Dict[str, str]
    ontology_id: str
    created_by: Optional[str] = None

    @classmethod
    def type_name(cls):
        return "App"


APP_FIELD_NAMES = list(App.model_json_schema()['properties'].keys())
