from abc import ABC
from io import BytesIO
from typing import Callable, Optional, Union
from typing_extensions import Literal
import numpy as np
import requests
from PIL import Image
from google.api_core import retry
from pydantic import BaseModel
from pydantic import root_validator

from .base_data import BaseData
from ..types import TypedArray


class RasterData(BaseModel, ABC):
    """Represents an image or segmentation mask.
    """
    im_bytes: Optional[bytes] = None
    file_path: Optional[str] = None
    url: Optional[str] = None
    arr: Optional[TypedArray[Literal['uint8']]] = None

    @classmethod
    def from_2D_arr(cls, arr: Union[TypedArray[Literal['uint8']],
                                    TypedArray[Literal['int']]],
                    **kwargs) -> "RasterData":
        """Construct from a 2D numpy array

        Args:
            arr: uint8 compatible numpy array

        Returns:
            RasterData
        """

        if len(arr.shape) != 2:
            raise ValueError(
                f"Found array with shape {arr.shape}. Expected two dimensions [H, W]"
            )

        if not np.issubdtype(arr.dtype, np.integer):
            raise ValueError("Array must be an integer subtype")

        if np.can_cast(arr, np.uint8):
            arr = arr.astype(np.uint8)
        else:
            raise ValueError(
                "Could not cast array to uint8, check that values are between 0 and 255"
            )

        arr = np.stack((arr,) * 3, axis=-1)
        return cls(arr=arr, **kwargs)

    def bytes_to_np(self, image_bytes: bytes) -> np.ndarray:
        """
        Converts image bytes to a numpy array
        Args:
            image_bytes (bytes): PNG encoded image
        Returns:
            numpy array representing the image
        """
        arr = np.array(Image.open(BytesIO(image_bytes)))
        if len(arr.shape) == 2:
            arr = np.stack((arr,) * 3, axis=-1)
        return arr[:, :, :3]

    def np_to_bytes(self, arr: np.ndarray) -> bytes:
        """
        Converts a numpy array to bytes
        Args:
            arr (np.array): numpy array representing the image
        Returns:
            png encoded bytes
        """
        if len(arr.shape) != 3:
            raise ValueError(
                "unsupported image format. Must be 3D ([H,W,C])."
                f"Use {self.__class__.__name__}.from_2D_arr to construct from 2D"
            )
        if arr.dtype != np.uint8:
            raise TypeError(f"image data type must be uint8. Found {arr.dtype}")

        im_bytes = BytesIO()
        Image.fromarray(arr).save(im_bytes, format="PNG")
        return im_bytes.getvalue()

    @property
    def value(self) -> np.ndarray:
        """
        Property that unifies the data access pattern for all references to the raster.

        Returns:
            numpy representation of the raster
        """
        if self.arr is not None:
            return self.arr
        if self.im_bytes is not None:
            return self.bytes_to_np(self.im_bytes)
        elif self.file_path is not None:
            with open(self.file_path, "rb") as img:
                im_bytes = img.read()
            self.im_bytes = im_bytes
            arr = self.bytes_to_np(im_bytes)
            return arr
        elif self.url is not None:
            im_bytes = self.fetch_remote()
            self.im_bytes = im_bytes
            return self.bytes_to_np(im_bytes)
        else:
            raise ValueError("Must set either url, file_path or im_bytes")

    def set_fetch_fn(self, fn):
        object.__setattr__(self, 'fetch_remote', lambda: fn(self))

    @retry.Retry(deadline=60.)
    def fetch_remote(self) -> bytes:
        """
        Method for accessing url.

        If url is not publicly accessible or requires another access pattern
        simply override this function
        """
        response = requests.get(self.url)
        response.raise_for_status()
        return response.content

    @retry.Retry(deadline=30.)
    def create_url(self, signer: Callable[[bytes], str]) -> str:
        """
        Utility for creating a url from any of the other image representations.

        Args:
            signer: A function that accepts bytes and returns a signed url.
        Returns:
            url for the raster data
        """
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

    @root_validator()
    def validate_args(cls, values):
        file_path = values.get("file_path")
        im_bytes = values.get("im_bytes")
        url = values.get("url")
        arr = values.get("arr")
        uid = values.get('uid')
        if uid == file_path == im_bytes == url == None and arr is None:
            raise ValueError(
                "One of `file_path`, `im_bytes`, `url`, `uid` or `arr` required."
            )
        if arr is not None:
            if arr.dtype != np.uint8:
                raise TypeError(
                    "Numpy array representing segmentation mask must be np.uint8"
                )
            elif len(arr.shape) != 3:
                raise ValueError(
                    "unsupported image format. Must be 3D ([H,W,C])."
                    f"Use {cls.__name__}.from_2D_arr to construct from 2D")
        return values

    def __repr__(self) -> str:
        symbol_or_none = lambda data: '...' if data is not None else None
        return f"{self.__class__.__name__}(im_bytes={symbol_or_none(self.im_bytes)}," \
               f"file_path={self.file_path}," \
               f"url={self.url}," \
               f"arr={symbol_or_none(self.arr)})"

    class Config:
        # Required for sharing references
        copy_on_model_validation = False
        # Required for discriminating between data types
        extra = 'forbid'


class MaskData(RasterData):
    """Used to represent a segmentation Mask

    All segments within a mask must be mutually exclusive. At a
    single cell, only one class can be present. All Mask data is
    converted to a [H,W,3] image. Classes are

    >>> # 3x3 mask with two classes and back ground
    >>> MaskData.from_2D_arr([
    >>>    [0, 0, 0],
    >>>    [1, 1, 1],
    >>>    [2, 2, 2],
    >>>])

    Args:
        im_bytes: Optional[bytes] = None
        file_path: Optional[str] = None
        url: Optional[str] = None
        arr: Optional[TypedArray[Literal['uint8']]] = None
    """


class ImageData(RasterData, BaseData):
    ...
