from typing import Optional

from pydantic import BaseModel


class BaseData(BaseModel):
    """
    Base class for objects representing data.
    This class shouldn't directly be used
    """
    external_id: Optional[str] = None
    uid: Optional[str] = None
