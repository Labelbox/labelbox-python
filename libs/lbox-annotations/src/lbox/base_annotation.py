import abc
from typing import Any, Dict, Optional
from uuid import UUID, uuid4

from pydantic import ConfigDict, Field, PrivateAttr

from .feature_schema import FeatureSchema


class BaseAnnotation(FeatureSchema, abc.ABC):
    """Base annotation class. Shouldn't be directly instantiated"""

    _uuid: Optional[UUID] = PrivateAttr()
    extra: Dict[str, Any] = Field(default_factory=dict, exclude=True)

    model_config = ConfigDict(extra="allow")

    def __init__(self, **data):
        super().__init__(**data)
        extra_uuid = data.get("extra", {}).get("uuid")
        self._uuid = data.get("_uuid") or extra_uuid or uuid4()
