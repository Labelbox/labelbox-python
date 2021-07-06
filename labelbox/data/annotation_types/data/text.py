from typing import Dict, Any
from pydantic.class_validators import root_validator
from pydantic.error_wrappers import ValidationError

import requests
import numpy as np
from pydantic import BaseModel
from typing import Optional
from labelbox.data.annotation_types.reference import DataRowRef


class TextData(BaseModel):
    file_path: Optional[str] = None
    text: Optional[str] = None
    url: Optional[str] = None
    data_row_ref: Optional[DataRowRef] = None
    _cache = True

    @property
    def numpy(self) -> np.ndarray:
        # This is where we raise the exception..
        if self.text:
            return np.array(self.text)
        elif self.file_path:
            # TODO: Throw error if file doesn't exist.
            # What does imread do?
            with open(self.file_path, "r") as file:
                text = file.read()
            if self._cache:
                self.text = text
            return np.array(text)
        elif self.url:
            response = requests.get(self.url)
            response.raise_for_status()
            text = response.text
            if self._cache:
                self.text = text
            return np.array(text)
        else:
            raise ValueError("Must set either url, file_path or im_bytes")

    @root_validator
    def validate_date(cls, values):
        file_path = values.get("file_path")
        im_bytes = values.get("text")
        url = values.get("url")
        if file_path == im_bytes == url == None:
            raise ValidationError(
                "One of `file_path`, `im_bytes`, or `url` required.")
        return values
