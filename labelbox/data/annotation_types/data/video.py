import logging
from uuid import uuid4
from typing import Generator, Optional, Tuple, Dict, Any

import cv2
import urllib.request
import numpy as np
from pydantic import BaseModel, ValidationError, root_validator

from labelbox.data.annotation_types.reference import DataRowRef

logger = logging.getLogger(__name__)


class VideoData(BaseModel):
    file_path: Optional[str] = None
    url: Optional[str] = None
    frames: Optional[Dict[int, np.ndarray]] = None
    data_row_ref: Optional[DataRowRef] = None

    def load_frames(self, overwrite: bool = False) -> None:
        logger.warning(
            "Loading the video into individual frames. This will use a lot of memory"
        )
        if self.frames and not overwrite:
            return

        for count, frame in self.frame_generator():
            self.frames[count] = frame

    def frame_generator(self, load_frames = False) -> Generator[Tuple[int, np.ndarray], None, None]:
        if self.frames is not None:
            for idx, img in self.frames.items():
                yield idx, img
            return
        elif self.url and not self.file_path:
            file_path = f"/tmp/{uuid4()}.mp4"
            logger.info(f"Downloading the video locally to {file_path}")
            urllib.request.urlretrieve(self.url, file_path)
            self.file_path = file_path
                # TODO: If the filepath exists but there was no data we should use the url (and the opposite too)

        vidcap = cv2.VideoCapture(self.file_path)

        success, img = vidcap.read()
        count = 0
        self.frames = {}
        while success:
            img = img[:, :, ::-1]
            yield count, img
            if load_frames:
                self.frames[count] = img
            success, img = vidcap.read()
            count += 1

    def __getitem__(self, idx: int) -> np.ndarray:
        if self.frames is None:
            raise ValueError(
                "Cannot select by index without iterating over the entire video or loading all frames."
            )
        return self.frames[idx]

    @root_validator
    def validate_data(cls, values):
        file_path = values.get("file_path")
        im_bytes = values.get("url")
        url = values.get("frames")
        if file_path == im_bytes == url == None:
            raise ValidationError(
                "One of `file_path`, `frames`, or `url` required.")
        return values

    class Config:
        # TODO: Create numpy array type
        arbitrary_types_allowed = True
