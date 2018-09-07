"""
Module for interacting with predictions on labelbox.com
"""
import collections
import rasterio.features

# TODO: path simplification
def vectorize_to_v4_label(segmentation_map, legend):
    """Converts a segmentation map into polygons.

    Given a raster pixel-wise array of predictions, this method
    converts it into vectorized polygons suitable for use in
    as `prediction`s in Labelbox's image-segmentation front ends.

    A pixel value of 0 is used to denote background pixels and
    the remaining pixel values are interpereted following the
    `legend` argument.

    Args:
        segmentation_map: A width x height array.
        legend: A dictonary mapping pixel values
            used in `segmentation_map` to semantic
            class names.

    Returns:
        A dictionary suitable for use as a `prediction`
        in image-segmentation v4 frontend after calling `json.dumps`.
    """
    assert len(segmentation_map.shape) == 2, \
            'Segmentation maps must be numpy arrays with shape (width, height)'
    label = collections.defaultdict(lambda: [])
    for polygon, pixel_value in rasterio.features.shapes(segmentation_map):
        pixel_value = int(pixel_value)
        # ignore background (denoted by pixel value 0)
        if pixel_value in legend and pixel_value is not 0:
            label[legend[pixel_value]].append({
                'geometry': [
                    {'x': int(p[0]), 'y': int(p[1])}
                    for p in polygon['coordinates'][0]
                    ]
                })
    return label
