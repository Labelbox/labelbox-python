from typing import Any, Dict
from labelbox.data.annotation_types.feature import FeatureSchema
from pydantic import BaseModel


class ScalarMetric(BaseModel):
    """ Class representing metrics """
    value: float
    extra: Dict[str, Any] = {}
