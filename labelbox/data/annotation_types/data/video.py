from labelbox.data.annotation_types.reference import DataRowRef
import logging

from typing import Optional
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
from uuid import uuid4
import logging

logger = logging.getLogger(__name__)


@marshmallow_dataclass.dataclass
class VideoData:
    file_path: Optional[str] = default_none()
    url: Optional[str] = default_none()
    frames: Optional[Dict[int, np.ndarray]] = default_none()
    data_row_ref: DataRowRef = default_none()
    _numpy = None
    _cache = False

    def process(self, overwrite = False):
        logger.warning("Loading the video into individual frames. This will use a lot of memory")
        if not self._cache:
            raise ValueError("set `VideoData._cache = True` to cache the data")

        if self.frames and not overwrite:
            return

        for count, frame in self.frame_generator:
            self.frames[count] = frame

    def bytes_to_np(self, image_bytes):
        return np.array(Image.open(BytesIO(image_bytes)))

    def frame_generator(self):
        if self.frames is not None:
            for idx, img in self.frames.items():
                yield idx,img
        elif self.url and not self.file_path:
            file_path = f"/tmp/{uuid4()}.mp4"
            logger.info(f"Downloading the video locally to {file_path}")
            vidcap = cv2.VideoCapture(file_path)
            with open(file_path, "wb") as file:
                res = requests.get(self.url)
                res.raise_for_status()
                file.write(res.content)
                self.file_path = file_path

        vidcap = cv2.VideoCapture(self.file_path)

        success, img = vidcap.read()
        count = 0
        while success:
            img = img[:,:,::-1]
            yield count,
            if self._cache:
                self.frames[count] = img
            success, img = vidcap.read()

    def __getitem__(self, idx):
        if self.frames is None:
            raise ValueError("Cannot index video until frames have been proessed.")
        return self.frames[idx]

    @validates_schema
    def validate_content(self, data: Dict[str, Any], **_) -> None:
        file_path = data.get("file_path")
        im_bytes = data.get("im_bytes")
        url = data.get("url")
        if not (file_path or im_bytes or url):
            raise ValidationError("One of `file_path`, `im_bytes`, or `url` required.")
