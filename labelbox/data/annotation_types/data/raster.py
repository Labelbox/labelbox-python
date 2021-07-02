from labelbox.data.annotation_types.reference import DataRowReference
import logging

import requests
from marshmallow.decorators import validates_schema
import cv2
import marshmallow_dataclass
import numpy as np
from marshmallow import ValidationError
from typing import Dict, Any, Union
from io import BytesIO
from PIL import Image
from labelbox.data.annotation_types.marshmallow import default_none
from labelbox import Entity


@marshmallow_dataclass.dataclass
class RasterData:
    """


    """
    im_bytes: bytes = default_none()
    file_path: str = default_none()
    url: str = default_none()
    data_row_ref: DataRowReference = default_none()
    _numpy = None
    _cache = True

    def bytes_to_np(self, image_bytes):
        return np.array(Image.open(BytesIO(image_bytes)))

    @property
    def numpy(self):
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
