from labelbox import Client

from typing import Dict, Any, Tuple
from skimage import measure
from io import BytesIO
from PIL import Image
import numpy as np
import uuid


def create_boxes_ndjson(datarow_id: str, schema_id: str, top: float,
                        left: float, bottom: float,
                        right: float) -> Dict[str, Any]:
    """
    * https://docs.labelbox.com/data-model/en/index-en#bounding-box

    Args:
        datarow_id (str): id of the data_row (in this case image) to add this annotation to
        schema_id (str): id of the bbox tool in the current ontology
        top, left, bottom, right (int): pixel coordinates of the bbox
    Returns:
        ndjson representation of a bounding box
    """
    return {
        "uuid": str(uuid.uuid4()),
        "schemaId": schema_id,
        "dataRow": {
            "id": datarow_id
        },
        "bbox": {
            "top": int(top),
            "left": int(left),
            "height": int(bottom - top),
            "width": int(right - left)
        }
    }


def create_polygon_ndjson(datarow_id: str, schema_id: str,
                          segmentation_mask: np.ndarray) -> Dict[str, Any]:
    """
    * https://docs.labelbox.com/data-model/en/index-en#polygon

    Args:
        datarow_id (str): id of the data_row (in this case image) to add this annotation to
        schema_id (str): id of the bbox tool in the current ontology
        segmentation_mask (np.ndarray): Segmentation mask of size (image_h, image_w)
            - Seg mask is turned into a polygon since polygons aren't directly inferred.
    Returns:
        ndjson representation of a polygon
    """
    contours = measure.find_contours(segmentation_mask, 0.5)
    #Note that complex polygons could break.
    pts = contours[0].astype(np.int32)
    pts = np.roll(pts, 1, axis=-1)
    pts = [{'x': int(x), 'y': int(y)} for x, y in pts]
    return {
        "uuid": str(uuid.uuid4()),
        "schemaId": schema_id,
        "dataRow": {
            "id": datarow_id
        },
        "polygon": pts
    }


def create_mask_ndjson(client: Client, datarow_id: str, schema_id: str,
                       segmentation_mask: np.ndarray,
                       color: Tuple[int, int, int]) -> Dict[str, Any]:
    """
    Creates a mask for each object in the image
    * https://docs.labelbox.com/data-model/en/index-en#segmentation-mask

    Args:
        client (labelbox.Client): labelbox client used for uploading seg mask to google cloud storage
        datarow_id (str): id of the data_row (in this case image) to add this annotation to
        schema_id (str): id of the segmentation tool in the current ontology
        segmentation_mask is a segmentation mask of size (image_h, image_w)
        color ( Tuple[int,int,int]): rgb color to convert binary mask into 3D colorized mask
    Return:
        ndjson representation of a segmentation mask
    """

    colorize = np.concatenate(
        ([segmentation_mask[..., np.newaxis] * c for c in color]), axis=2)
    img_bytes = BytesIO()
    Image.fromarray(colorize).save(img_bytes, format="PNG")
    #* Use your own signed urls so that you can resign the data
    #* This is just to make the demo work
    url = client.upload_data(content=img_bytes.getvalue(), sign=True)
    return {
        "uuid": str(uuid.uuid4()),
        "schemaId": schema_id,
        "dataRow": {
            "id": datarow_id
        },
        "mask": {
            "instanceURI": url,
            "colorRGB": color
        }
    }


def create_point_ndjson(datarow_id: str, schema_id: str, top: float,
                        left: float, bottom: float,
                        right: float) -> Dict[str, Any]:
    """
    * https://docs.labelbox.com/data-model/en/index-en#point

    Args:
        datarow_id (str): id of the data_row (in this case image) to add this annotation to
        schema_id (str): id of the point tool in the current ontology
        t, l, b, r (int): top, left, bottom, right pixel coordinates of the bbox
        - The model doesn't directly predict points, so we grab the centroid of the predicted bounding box
    Returns:
        ndjson representation of a polygon
    """
    return {
        "uuid": str(uuid.uuid4()),
        "schemaId": schema_id,
        "dataRow": {
            "id": datarow_id
        },
        "point": {
            "x": int((left + right) / 2.),
            "y": int((top + bottom) / 2.),
        }
    }
