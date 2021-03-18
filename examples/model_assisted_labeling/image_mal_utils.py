import cv2
import numpy as np
import requests
from io import BytesIO
from PIL import Image

def visualize_bbox_ndjsons(image, bbox_ndjsons, color):
    for bbox_ndjson in bbox_ndjsons:
        bbox = bbox_ndjson['bbox']
        start_point = (int(bbox['left']), int(bbox['top']))
        end_point = (int(bbox['left'] + bbox['width']), int(bbox['top'] + bbox['height']))
        image = cv2.rectangle(image, start_point, end_point, thickness = 2, color = color)
    return image

def visualize_poly_ndjsons(image, poly_ndjsons, color):
    for poly_ndjson in poly_ndjsons:
        pts = [[poly['x'], poly['y']] for poly in poly_ndjson['polygon']]
        pts = np.array(pts).astype(np.int32)
        image = cv2.polylines(image,[pts],True,color, thickness = 2)
    return image

def visualize_point_ndjsons(image, point_ndjsons, color):
    for point_ndjson in point_ndjsons:
        point = point_ndjson['point']
        image = cv2.circle(image, (point['x'],point['y']), radius=10, color=color, thickness=-1)
    return image

def visualize_mask_ndjsons(image, mask_ndjsons):
    masks = []
    for ndjson in mask_ndjsons:
        instanceURI = ndjson['mask']['instanceURI']
        masks.append(np.array(Image.open(BytesIO(requests.get(instanceURI).content))))
    masks = np.sum(masks, axis = 0).astype(np.uint8)
    return cv2.addWeighted(image, 0.7, masks, 0.3, 0)


