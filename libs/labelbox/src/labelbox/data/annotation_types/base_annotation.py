import abc
from uuid import UUID, uuid4
from typing import Any, Dict, Optional
from labelbox import pydantic_compat

from .feature import FeatureSchema


class BaseAnnotation(FeatureSchema, abc.ABC):
    """ Base annotation class. Shouldn't be directly instantiated
    """
    _uuid: Optional[UUID] = pydantic_compat.PrivateAttr()
    extra: Dict[str, Any] = {}

    def __init__(self, **data):
        super().__init__(**data)
        extra_uuid = data.get("extra", {}).get("uuid")
        self._uuid = data.get("_uuid") or extra_uuid or uuid4()
