import cv2
import numpy as np
import requests
from io import BytesIO
from PIL import Image
from typing import List, Dict, Any, Tuple


def visualize_bbox_ndjsons(image: np.ndarray, bbox_ndjsons: List[Dict[str,
                                                                      Any]],
                           color: Tuple[int, int, int]) -> np.ndarray:
    """
    Draws a collection of ndjson bounding box examples onto an image. 
    * Useful for validation
    
    Args:
        image (np.ndarray): Image to draw bounding boxes on
        bbox_ndjsons (List[Dict[str, Any]]): List of ndjson examples
        color (Tuple[int,int,int]) : Color of the bounding box in rgb 
    Returns:
        image with bounding boxes drawn on it
    """
    for bbox_ndjson in bbox_ndjsons:
        bbox = bbox_ndjson["bbox"]
        start_point = (int(bbox["left"]), int(bbox["top"]))
        end_point = (int(bbox["left"] + bbox["width"]),
                     int(bbox["top"] + bbox["height"]))
        image = cv2.rectangle(image,
                              start_point,
                              end_point,
                              thickness=2,
                              color=color)
    return image


def visualize_poly_ndjsons(image: np.ndarray, poly_ndjsons: List[Dict[str,
                                                                      Any]],
                           color: Tuple[int, int, int]) -> np.ndarray:
    """
    Draws a collection of ndjson polygon examples onto an image. 
    * Useful for validation
    
    Args:
        image (np.ndarray): Image to draw bounding boxes on
        poly_ndjsons (List[Dict[str, Any]]): List of ndjson examples
        color (Tuple[int,int,int]) : Color of the polygon in rgb 
    Returns:
        image with polygons drawn on it
    """
    for poly_ndjson in poly_ndjsons:
        pts = [[poly["x"], poly["y"]] for poly in poly_ndjson["polygon"]]
        pts = np.array(pts).astype(np.int32)
        image = cv2.polylines(image, [pts], True, color, thickness=2)
    return image


def visualize_point_ndjsons(image: np.ndarray, point_ndjsons: List[Dict[str,
                                                                        Any]],
                            color: Tuple[int, int, int]) -> np.ndarray:
    """
    Draws a collection of ndjson point examples onto an image. 
    * Useful for validation
    
    Args:
        image (np.ndarray): Image to draw bounding boxes on
        point_ndjsons (List[Dict[str, Any]]): List of ndjson examples
        color (Tuple[int,int,int]) : Color of the point in rgb
    Returns:
        image with points drawn on it
    """
    for point_ndjson in point_ndjsons:
        point = point_ndjson["point"]
        image = cv2.circle(image, (point["x"], point["y"]),
                           radius=10,
                           color=color,
                           thickness=-1)
    return image


def visualize_mask_ndjsons(image: np.ndarray,
                           mask_ndjsons: List[Dict[str, Any]]) -> np.ndarray:
    """
    Overlays the mask onto the image
    * Useful for validation
    
    Args:
        image (np.ndarray): Image to draw bounding boxes on
        mask_ndjsons (List[Dict[str, Any]]): List of ndjson examples
    Returns:
        image with mask overlaid onto it
    """
    masks = []
    for ndjson in mask_ndjsons:
        instanceURI = ndjson["mask"]["instanceURI"]
        masks.append(
            np.array(Image.open(BytesIO(requests.get(instanceURI).content))))
    masks = np.sum(masks, axis=0).astype(np.uint8)
    return cv2.addWeighted(image, 0.7, masks, 0.3, 0)
