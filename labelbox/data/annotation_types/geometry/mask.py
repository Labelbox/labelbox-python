from typing import Callable, Optional, Tuple, Union

import numpy as np
from pydantic.class_validators import validator
from rasterio.features import shapes
from shapely.geometry import MultiPolygon, shape
import cv2

from ..data import MaskData
from .geometry import Geometry


class Mask(Geometry):
    """Mask used to represent a single class in a larger segmentation mask

    Example of a mutually exclusive class

    >>> arr = MaskData.from_2D_arr([
    >>>    [0, 0, 0],
    >>>    [1, 1, 1],
    >>>    [2, 2, 2],
    >>>])
    >>> annotations = [
    >>>    ObjectAnnotation(value=Mask(mask=arr, color=1), name="dog"),
    >>>    ObjectAnnotation(value=Mask(mask=arr, color=2), name="cat"),
    >>>]

    Args:
         mask (MaskData): An object containing the actual mask, `MaskData` can
            be shared across multiple `Masks` to more efficiently store data
            for mutually exclusive segmentations.
         color (Tuple[uint8, uint8, uint8]): RGB color or a single value
            indicating the values of the class in the `MaskData`
    """

    mask: MaskData
    color: Union[Tuple[int, int, int], int]

    @property
    def geometry(self):
        mask = self.draw(color=1)
        polygons = (
            shape(shp)
            for shp, val in shapes(mask, mask=None)
            # ignore if shape is area of smaller than 1 pixel
            if val >= 1)
        return MultiPolygon(polygons).__geo_interface__

    def draw(self,
             height: Optional[int] = None,
             width: Optional[int] = None,
             canvas: Optional[np.ndarray] = None,
             color: Optional[Union[int, Tuple[int, int, int]]] = None,
             thickness=None) -> np.ndarray:
        """Converts the Mask object into a numpy array

        Args:
            height (int): Optionally resize mask height before drawing.
            width (int): Optionally resize mask width before drawing.
            canvas (np.ndarray): Optionall provide a canvas to draw on
            color (Union[int, Tuple[int,int,int]]): Color to draw the canvas.
                Defaults to using the encoded color in the mask.
                int will return the mask as a 1d array
                tuple[int,int,int] will return the mask as a 3d array
            thickness (None): Unused, exists for a consistent interface.

        Returns:
            np.ndarray representing only this object
                as opposed to the mask that this object references which might have multiple objects determined by colors
        """

        mask = self.mask.value
        mask = np.alltrue(mask == self.color, axis=2).astype(np.uint8)

        if height is not None or width is not None:
            mask = cv2.resize(mask,
                              (width or mask.shape[1], height or mask.shape[0]))

        dims = [mask.shape[0], mask.shape[1]]
        color = color or self.color
        if isinstance(color, (tuple, list)):
            dims = dims + [len(color)]

        canvas = canvas if canvas is not None else np.zeros(tuple(dims),
                                                            dtype=np.uint8)
        canvas[mask.astype(np.bool)] = color
        return canvas

    def create_url(self, signer: Callable[[bytes], str]) -> str:
        """
        Update the segmentation mask to have a url.
        Only update the mask if it doesn't already have a url

        Args:
            signer: A function that accepts bytes and returns a signed url.
        Returns:
            the url for the mask
        """
        return self.mask.create_url(signer)

    @validator('color')
    def is_valid_color(cls, color):
        if isinstance(color, (tuple, list)):
            if len(color) == 1:
                color = [color[0]] * 3
            if len(color) != 3:
                raise ValueError(
                    "Segmentation colors must be either a (r,g,b) tuple or a single grayscale value"
                )
            elif not all([0 <= c <= 255 for c in color]):
                raise ValueError(
                    f"All rgb colors must be between 0 and 255. Found : {color}"
                )
        elif not (0 <= color <= 255):
            raise ValueError(
                f"All rgb colors must be between 0 and 255. Found : {color}")

        return color
