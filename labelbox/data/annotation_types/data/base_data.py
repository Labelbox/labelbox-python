from typing import Optional

from pydantic import BaseModel


class BaseData(BaseModel):
    external_id: Optional[str] = None
    uid: Optional[str] = None
