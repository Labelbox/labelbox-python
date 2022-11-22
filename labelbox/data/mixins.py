from typing import Optional

from pydantic import BaseModel, validator

from labelbox.exceptions import ConfidenceNotSupportedException


class ConfidenceMixin(BaseModel):
    confidence: Optional[float] = None

    @validator('confidence')
    def confidence_valid_float(cls, value):
        if value is None:
            return value
        if not isinstance(value, (int, float)) or not 0 <= value <= 1:
            raise ValueError('must be a number within [0,1] range')
        return value

    def dict(self, *args, **kwargs):
        res = super().dict(*args, **kwargs)
        if 'confidence' in res and res['confidence'] is None:
            res.pop('confidence')
        return res


class ConfidenceNotSupportedMixin:

    def __new__(cls, *args, **kwargs):
        if 'confidence' in kwargs:
            raise ConfidenceNotSupportedException(
                'Confidence is not supported for this annotaiton type yet')
        return super().__new__(cls)
