from typing import Callable, Optional, Tuple, Union, Dict, List

import numpy as np
from pydantic.class_validators import validator
from shapely.geometry import MultiPolygon, Polygon
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
    def geometry(self) -> Dict[str, Tuple[int, int, int]]:
        mask = self.draw(color=1)
        contours, hierarchy = cv2.findContours(image=mask,
                                               mode=cv2.RETR_TREE,
                                               method=cv2.CHAIN_APPROX_NONE)

        holes = []
        external_contours = []
        for i in range(len(contours)):
            if hierarchy[0, i, 3] != -1:
                #determined to be a hole based on contour hierarchy
                holes.append(contours[i])
            else:
                external_contours.append(contours[i])

        external_polygons = self._extract_polygons_from_contours(
            external_contours)
        holes = self._extract_polygons_from_contours(holes)

        if not external_polygons.is_valid:
            external_polygons = external_polygons.buffer(0)

        if not holes.is_valid:
            holes = holes.buffer(0)

        return external_polygons.difference(holes).__geo_interface__

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
        canvas[mask.astype(bool)] = color
        return canvas

    def _extract_polygons_from_contours(self, contours: List) -> MultiPolygon:
        contours = map(np.squeeze, contours)
        filtered_contours = filter(lambda contour: len(contour) > 2, contours)
        polygons = map(Polygon, filtered_contours)
        return MultiPolygon(polygons)

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
