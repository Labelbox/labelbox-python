from typing import Dict, Any, Optional
from io import BytesIO

from PIL import Image
import numpy as np
import requests
from pydantic import BaseModel, ValidationError, root_validator

from labelbox.data.annotation_types.reference import DataRowRef


class RasterData(BaseModel):
    """

    """
    im_bytes: Optional[bytes] = None
    file_path: Optional[str] = None
    url: Optional[str] = None
    data_row_ref: Optional[DataRowRef] = None
    _cache = True

    def bytes_to_np(self, image_bytes: bytes) -> np.ndarray:
        return np.array(Image.open(BytesIO(image_bytes)))

    @property
    def numpy(self) -> np.ndarray:
        # This is where we raise the exception..
        if self.im_bytes is not None:
            return self.bytes_to_np(self.im_bytes)
        elif self.file_path is not None:
            # TODO: Throw error if file doesn't exist.
            # What does imread do?
            with open(self.file_path, "rb") as img:
                im_bytes = img.read()
            if self._cache:
                self.im_bytes = im_bytes
            return self.bytes_to_np(im_bytes)
        elif self.url is not None:
            response = requests.get(self.url)
            response.raise_for_status()
            im_bytes = response.content
            if self._cache:
                self.im_bytes = im_bytes
            return self.bytes_to_np(im_bytes)
        else:
            raise ValueError("Must set either url, file_path or im_bytes")

    @root_validator
    def validate_date(cls, values):
        file_path = values.get("file_path")
        im_bytes = values.get("im_bytes")
        url = values.get("url")
        if file_path == im_bytes == url == None:
            raise ValidationError(
                "One of `file_path`, `im_bytes`, or `url` required.")
        return values
