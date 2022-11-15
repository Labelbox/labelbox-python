from typing import Optional

from pydantic import BaseModel


class ConfidenceMixin(BaseModel):
    confidence: Optional[float] = None

    def dict(self, *args, **kwargs):
        res = super().dict(*args, **kwargs)
        if 'confidence' in res and res['confidence'] is None:
            res.pop('confidence')
        return res
