from typing import Callable, Dict, Any, Optional
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
    arr: Optional[np.ndarray] = None

    def bytes_to_np(self, image_bytes: bytes) -> np.ndarray:
        return np.array(Image.open(BytesIO(image_bytes)))

    def np_to_bytes(self, arr: np.ndarray) -> bytes:
        im_bytes = BytesIO()
        Image.fromarray(arr).save(im_bytes, format="PNG")
        return im_bytes.getvalue()

    @property
    def data(self) -> np.ndarray:
        # This is where we raise the exception..
        if self.arr is not None:
            return self.arr
        if self.im_bytes is not None:
            return self.bytes_to_np(self.im_bytes)
        elif self.file_path is not None:
            # TODO: Throw error if file doesn't exist.
            # What does imread do?
            with open(self.file_path, "rb") as img:
                im_bytes = img.read()
            self.im_bytes = im_bytes
            return self.bytes_to_np(im_bytes)
        elif self.url is not None:
            response = requests.get(self.url)
            response.raise_for_status()
            im_bytes = response.content
            self.im_bytes = im_bytes
            return self.bytes_to_np(im_bytes)
        else:
            raise ValueError("Must set either url, file_path or im_bytes")

    def create_url(self, signer: Callable[[bytes], str]) -> None:
        if self.url is not None:
            return self.url
        elif self.im_bytes is not None:
            self.url = signer(self.im_bytes)
        elif self.file_path is not None:
            with open(self.file_path, 'rb') as file:
                self.url = signer(file.read())
        elif self.arr is not None:
            self.url = signer(self.np_to_bytes(self.arr))
        else:
            raise ValueError(
                "One of url, im_bytes, file_path, arr must not be None.")
        return self.url

    @root_validator
    def validate_args(cls, values):
        file_path = values.get("file_path")
        im_bytes = values.get("im_bytes")
        url = values.get("url")
        arr = values.get("arr")
        if file_path == im_bytes == url == None and arr is None:
            raise ValidationError(
                "One of `file_path`, `im_bytes`, `url`, or `arr` required.")
        if arr is not None:
            if arr.dtype != np.uint8:
                raise ValidationError(
                    "Numpy array representing segmentation mask must be np.uint8"
                )
            elif len(arr.shape) not in [2, 3]:
                raise ValidationError(
                    f"Numpy array must have 2 or 3 dims. Found shape {arr.shape}"
                )
        return values

    class Config:
        # TODO: Create a type for numpy arrays
        arbitrary_types_allowed = True
        copy_on_model_validation = False
        extra = 'forbid'
