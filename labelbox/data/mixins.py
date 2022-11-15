from typing import Optional

from pydantic import BaseModel

from labelbox.exceptions import ConfidenceNotSupportedException


class ConfidenceMixin(BaseModel):
    confidence: Optional[float] = None

    def dict(self, *args, **kwargs):
        res = super().dict(*args, **kwargs)
        if 'confidence' in res and res['confidence'] is None:
            res.pop('confidence')
        return res


class ConfidenceNotSupportedMixin:
    def __new__(cls, *args, **kwargs):
        if 'confidence' in kwargs:
            raise ConfidenceNotSupportedException(
                'Confidence is not supported for this annotaiton type yet'
            )
        return super().__new__(cls)
