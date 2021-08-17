# Mapping can be used to select classes as instsance or segmentation
# By default polygon will be instance and segmentation will be semantic

# Will use subclasses too..
# checklist and radio will be turned into underscore delimitated names
from typing import Dict, Any
import os

from labelbox.data.annotation_types.collection import LabelCollection, LabelGenerator
from labelbox.data.serialization.coco.instance_dataset import CocoInstanceDataset
from labelbox.data.serialization.coco.panoptic_dataset import CocoPanopticDataset


def create_path_if_not_exists(path: str):
    if not os.path.exists(path):
        os.makedirs(path)


def validate_path(path, name):
    if not os.path.exists(path):
        raise ValueError(f"{name} {path} must exist")


class COCOConverter:
    """
    Note that this class is only compatible with image data.. it will ignore other data types.
    # TODO: Filter out video annotations..
    """

    def serialize_instances(labels: LabelCollection,
                            image_root: str) -> Dict[str, Any]:
        """
        Compatible with masks, polygons, and masks. Will turn masks into individual instances
        """
        create_path_if_not_exists(image_root)
        return CocoInstanceDataset.from_common(labels=labels,
                                               image_root=image_root).dict()

    def serialize_panoptic(labels: LabelCollection, image_root: str,
                           mask_root: str, all_stuff: bool = False) -> Dict[str, Any]:
        """
        All stuff turns every class into segmentation classes

        """
        create_path_if_not_exists(image_root)
        create_path_if_not_exists(mask_root)
        return CocoPanopticDataset.from_common(labels=labels,
                                               image_root=image_root,
                                               mask_root=mask_root, all_stuff=all_stuff).dict()

    @classmethod
    def deserialize_panoptic(cls, json_data: Dict[str, Any], image_root: str,
                             mask_root: str) -> LabelGenerator:
        validate_path(image_root, 'image_root')
        validate_path(mask_root, 'mask_root')
        objs = CocoPanopticDataset(**json_data)
        gen = objs.to_common(image_root, mask_root)
        return LabelGenerator(data=gen)

    @classmethod
    def deserialize_instances(cls, json_data: Dict[str, Any],
                              image_root: str) -> LabelGenerator:
        validate_path(image_root, 'image_root')
        objs = CocoInstanceDataset(**json_data)
        gen = objs.to_common(image_root)
        return LabelGenerator(data=gen)
