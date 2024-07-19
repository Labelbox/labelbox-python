import abc
from uuid import UUID, uuid4
from typing import Any, Dict, Optional

from .feature import FeatureSchema
from pydantic import PrivateAttr


class BaseAnnotation(FeatureSchema, abc.ABC):
    """ Base annotation class. Shouldn't be directly instantiated
    """
    _uuid: Optional[UUID] = PrivateAttr()
    extra: Dict[str, Any] = {}

    def __init__(self, **data):
        super().__init__(**data)
        extra_uuid = data.get("extra", {}).get("uuid")
        self._uuid = data.get("_uuid") or extra_uuid or uuid4()
