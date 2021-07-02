
from typing import Dict, Any
from io import BytesIO

import requests
import numpy as np
from PIL import Image
from marshmallow_dataclass import dataclass
from marshmallow import ValidationError
from marshmallow.decorators import validates_schema

from labelbox.data.annotation_types.marshmallow import default_none
from labelbox.data.annotation_types.reference import DataRowRef

@dataclass
class RasterData:
    """

    """

    im_bytes: bytes = default_none()
    file_path: str = default_none()
    url: str = default_none()
    data_row_ref: DataRowRef = default_none()
    _numpy = None
    _cache = True

    def bytes_to_np(self, image_bytes: bytes) -> np.ndarray:
        return np.array(Image.open(BytesIO(image_bytes)))

    @property
    def numpy(self) -> np.ndarray:
        # This is where we raise the exception..
        if self.im_bytes:
            return self.bytes_to_np(self.im_bytes)
        elif self.file_path:
            # TODO: Throw error if file doesn't exist.
            # What does imread do?
            with open(self.file_path, "rb") as img:
                im_bytes = img.read()
            if self._cache:
                self.im_bytes = im_bytes
            return self.bytes_to_np(im_bytes)
        elif self.url:
            response = requests.get(self.url)
            response.raise_for_status()
            im_bytes = response.content
            if self._cache:
                self.im_bytes = im_bytes
            return self.bytes_to_np(im_bytes)
        else:
            raise ValueError("Must set either url, file_path or im_bytes")

    @validates_schema
    def validate_content(self, data: Dict[str, Any], **_) -> None:
        file_path = data.get("file_path")
        im_bytes = data.get("im_bytes")
        url = data.get("url")
        if not (file_path or im_bytes or url):
            raise ValidationError("One of `file_path`, `im_bytes`, or `url` required.")
