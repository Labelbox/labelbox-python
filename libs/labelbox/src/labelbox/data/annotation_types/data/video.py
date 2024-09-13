import logging
import os
import urllib.request
from typing import Callable, Dict, Generator, Optional, Tuple
from typing_extensions import Literal
from uuid import uuid4

import cv2
import numpy as np
from google.api_core import retry

from .base_data import BaseData
from ..types import TypedArray

from pydantic import ConfigDict, model_validator

logger = logging.getLogger(__name__)


class VideoData(BaseData):
    """
    Represents video
    """

    file_path: Optional[str] = None
    url: Optional[str] = None
    frames: Optional[Dict[int, TypedArray[Literal["uint8"]]]] = None
    # Required for discriminating between data types
    model_config = ConfigDict(extra="forbid")

    def load_frames(self, overwrite: bool = False) -> None:
        """
        Loads all frames into memory at once in order to access in non-sequential order.
        This will use a lot of memory, especially for longer videos

        Args:
            overwrite: Replace existing frames
        """
        if self.frames and not overwrite:
            return

        for count, frame in self.frame_generator():
            if self.frames is None:
                self.frames = {}
            self.frames[count] = frame

    @property
    def value(self):
        return self.frame_generator()

    def frame_generator(
        self, cache_frames=False, download_dir="/tmp"
    ) -> Generator[Tuple[int, np.ndarray], None, None]:
        """
        A generator for accessing individual frames in a video.

        Args:
            cache_frames (bool): Whether or not to cache frames while iterating through the video.
            download_dir (str): Directory to save the video to. Defaults to `/tmp` dir
        """
        if self.frames is not None:
            for idx, frame in self.frames.items():
                yield idx, frame
            return
        elif self.url and not self.file_path:
            file_path = os.path.join(download_dir, f"{uuid4()}.mp4")
            logger.info("Downloading the video locally to %s", file_path)
            self.fetch_remote(file_path)
            self.file_path = file_path

        vidcap = cv2.VideoCapture(self.file_path)

        success, frame = vidcap.read()
        count = 0
        if cache_frames:
            self.frames = {}
        while success:
            frame = frame[:, :, ::-1]
            yield count, frame
            if cache_frames:
                self.frames[count] = frame
            success, frame = vidcap.read()
            count += 1

    def __getitem__(self, idx: int) -> np.ndarray:
        if self.frames is None:
            raise ValueError(
                "Cannot select by index without iterating over the entire video or loading all frames."
            )
        return self.frames[idx]

    def set_fetch_fn(self, fn):
        object.__setattr__(self, "fetch_remote", lambda: fn(self))

    @retry.Retry(deadline=15.0)
    def fetch_remote(self, local_path) -> None:
        """
        Method for downloading data from self.url

        If url is not publicly accessible or requires another access pattern
        simply override this function

        Args:
            local_path: Where to save the thing too.
        """
        urllib.request.urlretrieve(self.url, local_path)

    @retry.Retry(deadline=15.0)
    def create_url(self, signer: Callable[[bytes], str]) -> None:
        """
        Utility for creating a url from any of the other video references.

        Args:
            signer: A function that accepts bytes and returns a signed url.
        Returns:
            url for the video
        """
        if self.url is not None:
            return self.url
        elif self.file_path is not None:
            with open(self.file_path, "rb") as file:
                self.url = signer(file.read())
        elif self.frames is not None:
            self.file_path = self.frames_to_video(self.frames)
            self.url = self.create_url(signer)
        else:
            raise ValueError("One of url, file_path, frames must not be None.")
        return self.url

    def frames_to_video(
        self, frames: Dict[int, np.ndarray], fps=20, save_dir="/tmp"
    ) -> str:
        """
        Compresses the data by converting a set of individual frames to a single video.

        """
        file_path = os.path.join(save_dir, f"{uuid4()}.mp4")
        out = None
        for key in frames.keys():
            frame = frames[key]
            if out is None:
                out = cv2.VideoWriter(
                    file_path,
                    cv2.VideoWriter_fourcc(*"MP4V"),
                    fps,
                    frame.shape[:2],
                )
            out.write(frame)
        if out is None:
            return
        out.release()
        return file_path

    @model_validator(mode="after")
    def validate_data(self):
        file_path = self.file_path
        url = self.url
        frames = self.frames
        uid = self.uid
        global_key = self.global_key

        if uid == file_path == frames == url == global_key == None:
            raise ValueError(
                "One of `file_path`, `frames`, `uid`, `global_key` or `url` required."
            )
        return self

    def __repr__(self) -> str:
        return (
            f"VideoData(file_path={self.file_path},"
            f"frames={'...' if self.frames is not None else None},"
            f"url={self.url})"
        )
