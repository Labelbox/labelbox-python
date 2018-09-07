"""
Module for interacting with predictions on labelbox.com
"""

# TODO: path simplification
def raster_to_polygon(segmentation_map, legend):
    """Converts a segmentation map into polygons.

    Given a raster pixel-wise array of predictions, this method
    converts it into vectorized polygons suitable for use in
    as `prediction`s in Labelbox's image-segmentation front ends.

    Args:
        segmentation_map: A width x height array.
        legend: A dictonary mapping pixel values
            used in `segmentation_map` to semantic
            class names

    Returns:
        An object with keys given by the class names
        in `legend` and values equal to the vectorized
        polygons in `segmentation_map` which correspond
        to this class.
    """
    pass
