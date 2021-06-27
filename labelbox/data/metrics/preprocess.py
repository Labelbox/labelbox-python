import functools
from typing import List, Dict, Any, Union
from collections import defaultdict
import numpy as np  # type: ignore
from PIL import Image  # type: ignore
import requests
from io import BytesIO
from google.api_core import retry
import uuid

from labelbox.data.metrics.tool_types import ALL_TOOL_TYPES, SEGMENTATION_TOOLS, CLASSIFICATION_TOOLS
from labelbox.schema.bulk_import_request import NDAnnotation, NDBase


def get_tool(label: Dict[str, Any]):
    """Uses the keys in the label to determine the tool type """
    return next(iter(set(label) & ALL_TOOL_TYPES or SEGMENTATION_TOOLS))


def update_base(label: Dict[str, Any], datarow_id: str):
    """ Adds required field to the label json payload """
    label['uuid'] = str(uuid.uuid4())
    label['dataRow'] = {'id': datarow_id}


def label_to_ndannotation(label: Dict[str, Any],
                          datarow_id: str) -> NDAnnotation:
    """ Converts a label to an ndannotation. """
    tool = get_tool(label)

    # remove unecessary keys
    label = label.copy()
    update_base(label, datarow_id)
    # These only apply to vector tools....
    unused_keys = ['title', 'value', 'color', 'featureId', 'instanceURI']
    if tool in SEGMENTATION_TOOLS:
        label['mask'] = {
            'instanceURI': label['instanceURI'],
            # Matches the color in the seg masks in the exports
            'colorRGB': (255, 255, 255)
        }
    for unused_key in unused_keys:
        label.pop(unused_key, None)

    if tool not in CLASSIFICATION_TOOLS:
        label['classifications'] = clean_classifications(
            label.get('classifications', []), datarow_id)
    return NDAnnotation(**label)


def clean_classifications(classifications: List[Dict[str, Any]],
                          datarow_id: str) -> List[Dict[str, Any]]:
    """ Converts classifications to a format compatible with NDAnnotations """
    classifications = classifications.copy()
    unused_keys = ['title', 'value', 'color', 'featureId', 'instanceURI']
    for classification in classifications:
        update_base(classification, datarow_id)
        for unused_key in unused_keys:
            classification.pop(unused_key, None)
    return classifications


def create_schema_lookup(rows: List[NDBase]) -> Dict[str, List[Any]]:
    """ Takes a list of annotations and groups them by feature types """
    data = defaultdict(list)
    for row in rows:
        data[row.schemaId].append(row)
    return data


@retry.Retry(deadline=15.)
@functools.lru_cache(maxsize=256)
def url_to_numpy(mask_url: str) -> np.ndarray:
    """ Downloads an image and converts to a numpy array """
    return np.array(Image.open(BytesIO(requests.get(mask_url).content)))
