"Module for interacting with predictions on labelbox.com."
import collections
from typing import DefaultDict, Dict, List, Optional

import rasterio.features
from simplification.cutil import simplify_coords  # pylint: disable=no-name-in-module


def vectorize_to_v4_label(
        segmentation_map,
        legend: Dict[int, str],
        max_num_points: Optional[int] = 50) -> DefaultDict[str, List[dict]]:
    """Converts a segmentation map into polygons.

    Given a raster pixel wise array of predictions in `segmentation_map`,
    this method converts it into vectorized polygons suitable for use in as
    predictions in Labelbox image segmentation front ends.

    A pixel value of 0 is used to denote background pixels and
    the remaining pixel values are interpereted following the
    `legend` argument.

    Args:
        segmentation_map: A width x height array.
        legend: A dictonary mapping pixel values
            used in `segmentation_map` to semantic
            class names.
        max_num_points: The maximum number of points in the simplified path.
            If `None`, then no path simplification is performed.

    Returns:
        A dictionary suitable for use as a `prediction`
        in image-segmentation v4 frontend after calling `json.dumps`.
    """
    assert len(segmentation_map.shape) == 2, \
        'Segmentation maps must be numpy arrays with shape (width, height)'
    label: DefaultDict[str, List[dict]] = collections.defaultdict(lambda: [])
    for polygon, pixel_value in rasterio.features.shapes(segmentation_map):
        pixel_value = int(pixel_value)
        # ignore background (denoted by pixel value 0)
        if pixel_value in legend and pixel_value is not 0:
            xy_list = polygon['coordinates'][0]

            if max_num_points:
                epsilon = 0.001
                xy_list = simplify_coords(xy_list, epsilon)
                while len(xy_list) > max_num_points:
                    epsilon *= 2
                    xy_list = simplify_coords(xy_list, epsilon)

            geometry = []
            for point in xy_list:
                geometry.append({'x': int(point[0]), 'y': int(point[1])})

            class_name = legend[pixel_value]
            label[class_name].append({'geometry': geometry})
    return label
