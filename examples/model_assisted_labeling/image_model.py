import tensorflow as tf
import numpy as np
import cv2
from typing import Dict

#https://colab.research.google.com/github/tensorflow/tpu/blob/master/models/official/mask_rcnn/mask_rcnn_demo.ipynb#scrollTo=2oZWLz4xXsyQ

class_mappings = {1: 'person', 3: 'car', 28: 'umbrella', 31: 'handbag'}
session = tf.compat.v1.Session()


def load_model() -> None:
    """
    Loads model into session
    """
    saved_model_dir = 'gs://cloud-tpu-checkpoints/mask-rcnn/1555659850'
    _ = tf.compat.v1.saved_model.loader.load(session, ['serve'],
                                             saved_model_dir)


def predict(np_image_string: np.ndarray, min_score: float, height: int,
            width: int) -> Dict[str, np.ndarray]:
    """
    Args:
        np_image_string (np.ndarray): numpy array containing image bytes
        min_score (float): min detection threshold
        height: image height
        width: image width
    Returns:
        instance segmentation inference as a dict containing the class indices, boxes, and seg masks
    """
    num_detections, detection_boxes, detection_classes, detection_scores, detection_masks, image_info = session.run(
        [
            'NumDetections:0', 'DetectionBoxes:0', 'DetectionClasses:0',
            'DetectionScores:0', 'DetectionMasks:0', 'ImageInfo:0'
        ],
        feed_dict={'Placeholder:0': np_image_string})
    num_detections = np.squeeze(num_detections.astype(np.int32), axis=(0,))
    detection_scores = np.squeeze(detection_scores, axis=(0,))[0:num_detections]
    response = {
        'boxes':
            np.squeeze(detection_boxes * image_info[0, 2], axis=(0,))
            [0:num_detections],
        'class_indices':
            np.squeeze(detection_classes.astype(np.int32), axis=(0,))
            [0:num_detections],
    }
    ymin, xmin, ymax, xmax = np.split(response['boxes'], 4, axis=-1)
    instance_masks = np.squeeze(detection_masks, axis=(0,))[0:num_detections]
    processed_boxes = np.concatenate([xmin, ymin, xmax - xmin, ymax - ymin],
                                     axis=-1)
    response.update({
        'seg_masks':
            generate_segmentation_from_masks(instance_masks, processed_boxes,
                                             height, width)
    })
    keep_indices = detection_scores > min_score
    keep_indices = keep_indices & np.isin(response['class_indices'],
                                          list(class_mappings.keys()))
    for key in response:
        response[key] = response[key][keep_indices]
    return response


def expand_boxes(boxes: np.ndarray, scale: float) -> np.ndarray:
    """Expands an array of boxes by a given scale."""
    # Reference: https://github.com/facebookresearch/Detectron/blob/master/detectron/utils/boxes.py#L227  # pylint: disable=line-too-long
    # The `boxes` in the reference implementation is in [x1, y1, x2, y2] form,
    # whereas `boxes` here is in [x1, y1, w, h] form
    w_half = boxes[:, 2] * .5
    h_half = boxes[:, 3] * .5
    x_c = boxes[:, 0] + w_half
    y_c = boxes[:, 1] + h_half

    w_half *= scale
    h_half *= scale

    boxes_exp = np.zeros(boxes.shape)
    boxes_exp[:, 0] = x_c - w_half
    boxes_exp[:, 2] = x_c + w_half
    boxes_exp[:, 1] = y_c - h_half
    boxes_exp[:, 3] = y_c + h_half

    return boxes_exp


def generate_segmentation_from_masks(masks: np.ndarray,
                                     detected_boxes: np.ndarray,
                                     image_height: int,
                                     image_width: int,
                                     is_image_mask: bool = False) -> np.ndarray:
    """Generates segmentation result from instance masks.
    Args:
      masks: a numpy array of shape [N, mask_height, mask_width] representing the
        instance masks w.r.t. the `detected_boxes`.
      detected_boxes: a numpy array of shape [N, 4] representing the reference
        bounding boxes.
      image_height: an integer representing the height of the image.
      image_width: an integer representing the width of the image.
      is_image_mask: bool. True: input masks are whole-image masks. False: input
        masks are bounding-box level masks.
    Returns:
      segms: a numpy array of shape [N, image_height, image_width] representing
        the instance masks *pasted* on the image canvas.
    """

    _, mask_height, mask_width = masks.shape
    scale = max((mask_width + 2.0) / mask_width,
                (mask_height + 2.0) / mask_height)

    ref_boxes = expand_boxes(detected_boxes, scale)
    ref_boxes = ref_boxes.astype(np.int32)
    padded_mask = np.zeros((mask_height + 2, mask_width + 2), dtype=np.float32)
    segms = []
    for mask_ind, mask in enumerate(masks):
        im_mask = np.zeros((image_height, image_width), dtype=np.uint8)
        if is_image_mask:
            # Process whole-image masks.
            im_mask[:, :] = mask[:, :]
        else:
            # Process mask inside bounding boxes.
            padded_mask[1:-1, 1:-1] = mask[:, :]

            ref_box = ref_boxes[mask_ind, :]
            w = ref_box[2] - ref_box[0] + 1
            h = ref_box[3] - ref_box[1] + 1
            w = np.maximum(w, 1)
            h = np.maximum(h, 1)

            mask = cv2.resize(padded_mask, (w, h))
            mask = np.array(mask > 0.5, dtype=np.uint8)

            x_0 = max(ref_box[0], 0)
            x_1 = min(ref_box[2] + 1, image_width)
            y_0 = max(ref_box[1], 0)
            y_1 = min(ref_box[3] + 1, image_height)

            im_mask[y_0:y_1,
                    x_0:x_1] = mask[(y_0 - ref_box[1]):(y_1 - ref_box[1]),
                                    (x_0 - ref_box[0]):(x_1 - ref_box[0])]
        segms.append(im_mask)

    segms = np.array(segms)
    assert masks.shape[0] == segms.shape[0]
    return segms
