from typing import Any, Dict, Optional
from pydantic import BaseModel, ConfigDict, AliasGenerator
from pydantic.alias_generators import to_camel, to_snake
from labelbox.utils import _CamelCaseMixin


class App(_CamelCaseMixin):
    id: Optional[str] = None
    model_id: str
    name: str
    description: Optional[str] = None
    inference_params: Dict[str, Any]
    class_to_schema_id: Dict[str, str]
    ontology_id: str
    created_by: Optional[str] = None

    model_config = ConfigDict(protected_namespaces=())

    @classmethod
    def type_name(cls):
        return "App"


APP_FIELD_NAMES = list(App.model_json_schema()["properties"].keys())
