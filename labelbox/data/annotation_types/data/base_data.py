from abc import ABC
from typing import Optional, Dict, List, Any

from labelbox import pydantic_compat


class BaseData(pydantic_compat.BaseModel, ABC):
    """
    Base class for objects representing data.
    This class shouldn't directly be used
    """
    external_id: Optional[str] = None
    uid: Optional[str] = None
    global_key: Optional[str] = None
    media_attributes: Optional[Dict[str, Any]] = None
    metadata: Optional[List[Dict[str, Any]]] = None
