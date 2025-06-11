from typing import Callable, Dict, List, Optional, Tuple, Union

import cv2
import numpy as np
from pydantic import field_validator
from shapely.geometry import MultiPolygon, Polygon

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
        # Extract mask contours and build geometry
        mask = self.draw(color=1)
        contours, hierarchy = cv2.findContours(
            image=mask, mode=cv2.RETR_TREE, method=cv2.CHAIN_APPROX_NONE
        )

        holes = []
        external_contours = []
        for i in range(len(contours)):
            if hierarchy[0, i, 3] != -1:
                # determined to be a hole based on contour hierarchy
                holes.append(contours[i])
            else:
                external_contours.append(contours[i])

        external_polygons = self._extract_polygons_from_contours(
            external_contours
        )
        holes = self._extract_polygons_from_contours(holes)

        if not external_polygons.is_valid:
            external_polygons = external_polygons.buffer(0)

        if not holes.is_valid:
            holes = holes.buffer(0)

        # Get geometry result
        result_geometry = external_polygons.difference(holes)

        # Ensure consistent MultiPolygon format across shapely versions
        if (
            hasattr(result_geometry, "geom_type")
            and result_geometry.geom_type == "Polygon"
        ):
            result_geometry = MultiPolygon([result_geometry])

        # Get the geo interface and ensure consistent coordinate format
        geometry_dict = result_geometry.__geo_interface__

        # Normalize coordinates to ensure deterministic output across platforms
        if "coordinates" in geometry_dict:
            geometry_dict = self._normalize_polygon_coordinates(geometry_dict)

        return geometry_dict

    def _normalize_polygon_coordinates(self, geometry_dict):
        """Ensure consistent polygon coordinate format across platforms and shapely versions"""

        def clean_ring(ring):
            """Normalize ring coordinates to ensure consistent output across shapely versions"""
            if not ring or len(ring) < 3:
                return ring

            # Convert to tuples
            coords = [tuple(float(x) for x in coord) for coord in ring]

            # Remove the closing duplicate (last coordinate that equals first)
            if len(coords) > 1 and coords[0] == coords[-1]:
                coords = coords[:-1]

            # Remove any other consecutive duplicates
            cleaned = []
            for coord in coords:
                if not cleaned or cleaned[-1] != coord:
                    cleaned.append(coord)

            # For shapely 2.1.1 compatibility: ensure we start with the minimum coordinate
            # to get consistent ring orientation and starting point
            if len(cleaned) >= 3:
                min_idx = min(range(len(cleaned)), key=lambda i: cleaned[i])
                cleaned = cleaned[min_idx:] + cleaned[:min_idx]

            # Close the ring properly
            if len(cleaned) >= 3:
                cleaned.append(cleaned[0])

            return cleaned

        result = geometry_dict.copy()
        if geometry_dict["type"] == "MultiPolygon":
            normalized_coords = []
            for polygon in geometry_dict["coordinates"]:
                normalized_polygon = []
                for ring in polygon:
                    cleaned_ring = clean_ring(ring)
                    if (
                        len(cleaned_ring) >= 4
                    ):  # Minimum for a valid closed ring
                        normalized_polygon.append(tuple(cleaned_ring))
                if normalized_polygon:
                    normalized_coords.append(tuple(normalized_polygon))
            result["coordinates"] = normalized_coords

        return result

    def draw(
        self,
        height: Optional[int] = None,
        width: Optional[int] = None,
        canvas: Optional[np.ndarray] = None,
        color: Optional[Union[int, Tuple[int, int, int]]] = None,
        thickness=None,
    ) -> np.ndarray:
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
        mask = np.all(mask == self.color, axis=2).astype(np.uint8)

        if height is not None or width is not None:
            mask = cv2.resize(
                mask, (width or mask.shape[1], height or mask.shape[0])
            )

        dims = [mask.shape[0], mask.shape[1]]
        color = color or self.color
        if isinstance(color, (tuple, list)):
            dims = dims + [len(color)]

        canvas = (
            canvas
            if canvas is not None
            else np.zeros(tuple(dims), dtype=np.uint8)
        )
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

    @field_validator("color")
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
                f"All rgb colors must be between 0 and 255. Found : {color}"
            )

        return color
