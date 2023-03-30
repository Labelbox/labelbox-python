import abc
from uuid import UUID, uuid4
from typing import Any, Dict
from pydantic import PrivateAttr

from .feature import FeatureSchema


class BaseAnnotation(FeatureSchema, abc.ABC):
    """ Base annotation class. Shouldn't be directly instantiated
    """
    _uuid: UUID = PrivateAttr()
    extra: Dict[str, Any] = {}

    def __init__(self, **data):
        super().__init__(**data)
        extra_uuid = data.get("extra", {}).get("uuid")
        self._uuid = data.get("_uuid") or extra_uuid or uuid4()
