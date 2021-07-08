from typing import Dict, Any, Optional
from io import BytesIO

from PIL import Image
import numpy as np
import requests
from pydantic import ValidationError, root_validator

from labelbox.data.annotation_types.reference import DataRowRef


class RasterData(DataRowRef):
    """

    """
    im_bytes: Optional[bytes] = None
    file_path: Optional[str] = None
    url: Optional[str] = None
    _cache = True

    def bytes_to_np(self, image_bytes: bytes) -> np.ndarray:
        return np.array(Image.open(BytesIO(image_bytes)))

    @classmethod
    def from_np(cls, arr: np.array) -> "RasterData":
        if arr.dtype != np.uint8:
            raise TypeError("Numpy array representing segmentation mask must be np.uint8")
        elif len(arr.shape) not in [2,3]:
            raise ValueError(f"Numpy array must have 2 or 3 dims. Found shape {arr.shape}")
        im_bytes = BytesIO()
        Image.fromarray(arr).save(im_bytes, format = "PNG")
        return RasterData(im_bytes = im_bytes.getvalue())


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
