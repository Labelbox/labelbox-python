from typing import Dict, Any

import requests
import numpy as np
from marshmallow_dataclass import dataclass
from marshmallow import ValidationError
from marshmallow.decorators import validates_schema

from labelbox.data.annotation_types.marshmallow import default_none
from labelbox.data.annotation_types.reference import DataRowRef

@dataclass
class TextData:
    file_path: str = default_none()
    text: str = default_none()
    url: str = default_none()
    data_row_ref: DataRowRef = default_none()
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

    @validates_schema
    def validate_content(self, data: Dict[str, Any], **_) -> None:
        file_path = data.get("file_path")
        im_bytes = data.get("im_bytes")
        url = data.get("url")
        if not (file_path or im_bytes or url):
            raise ValidationError("One of `file_path`, `im_bytes`, or `url` required.")
