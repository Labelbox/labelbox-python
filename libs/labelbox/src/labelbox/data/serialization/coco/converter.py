from typing import Dict, Any, Union
from pathlib import Path
import os
import warnings

from ...annotation_types.collection import LabelCollection, LabelGenerator
from ...serialization.coco.instance_dataset import CocoInstanceDataset
from ...serialization.coco.panoptic_dataset import CocoPanopticDataset


def create_path_if_not_exists(
    path: Union[Path, str], ignore_existing_data=False
):
    path = Path(path)
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)
    elif not ignore_existing_data and os.listdir(path):
        raise ValueError(
            f"Directory `{path}`` must be empty. Or set `ignore_existing_data=True`"
        )
    return path


def validate_path(path: Union[Path, str], name: str):
    path = Path(path)
    if not path.exists():
        raise ValueError(f"{name} `{path}` must exist")
    return path


class COCOConverter:
    """
    Class for converting between coco and labelbox formats
    Note that this class is only compatible with image data.

    Subclasses are currently ignored.
    To use subclasses, manually flatten them before using the converter.
    """

    @staticmethod
    def serialize_instances(
        labels: LabelCollection,
        image_root: Union[Path, str],
        ignore_existing_data=False,
        max_workers=8,
    ) -> Dict[str, Any]:
        """
        Convert a Labelbox LabelCollection into an mscoco dataset.
        This function will only convert masks, polygons, and rectangles.
        Masks will be converted into individual instances.
        Use deserialize_panoptic to prevent masks from being split apart.

        Args:
            labels: A collection of labels to convert
            image_root: Where to save images to
            ignore_existing_data: Whether or not to raise an exception if images already exist.
                This exists only to support detectons panoptic fpn model which requires two mscoco payloads for the same images.
            max_workers : Number of workers to process dataset with. A value of 0 will process all data in the main process
        Returns:
            A dictionary containing labels in the coco object format.
        """

        warnings.warn(
            "You are currently utilizing COCOconverter for this action, which will be deprecated in a later release.",
            DeprecationWarning,
            stacklevel=2,
        )

        image_root = create_path_if_not_exists(image_root, ignore_existing_data)
        return CocoInstanceDataset.from_common(
            labels=labels, image_root=image_root, max_workers=max_workers
        ).model_dump()

    @staticmethod
    def serialize_panoptic(
        labels: LabelCollection,
        image_root: Union[Path, str],
        mask_root: Union[Path, str],
        all_stuff: bool = False,
        ignore_existing_data=False,
        max_workers: int = 8,
    ) -> Dict[str, Any]:
        """
        Convert a Labelbox LabelCollection into an mscoco dataset.
        This function will only convert masks, polygons, and rectangles.
        Masks will be converted into individual instances.
        Use deserialize_panoptic to prevent masks from being split apart.

        Args:
            labels: A collection of labels to convert
            image_root: Where to save images to
            mask_root: Where to save segmentation masks to
            all_stuff: If rectangle or polygon annotations are encountered, they will be treated as instances.
                To convert them to stuff class set `all_stuff=True`.
            ignore_existing_data: Whether or not to raise an exception if images already exist.
                This exists only to support detectons panoptic fpn model which requires two mscoco payloads for the same images.
            max_workers : Number of workers to process dataset with. A value of 0 will process all data in the main process.
        Returns:
            A dictionary containing labels in the coco panoptic format.
        """

        warnings.warn(
            "You are currently utilizing COCOconverter for this action, which will be deprecated in a later release.",
            DeprecationWarning,
            stacklevel=2,
        )

        image_root = create_path_if_not_exists(image_root, ignore_existing_data)
        mask_root = create_path_if_not_exists(mask_root, ignore_existing_data)
        return CocoPanopticDataset.from_common(
            labels=labels,
            image_root=image_root,
            mask_root=mask_root,
            all_stuff=all_stuff,
            max_workers=max_workers,
        ).model_dump()

    @staticmethod
    def deserialize_panoptic(
        json_data: Dict[str, Any],
        image_root: Union[Path, str],
        mask_root: Union[Path, str],
    ) -> LabelGenerator:
        """
        Convert coco panoptic data into the labelbox format (as a LabelGenerator).

        Args:
            json_data: panoptic data as a dict
            image_root: Path to local images that are referenced by the panoptic json
            mask_root: Path to local segmentation masks that are referenced by the panoptic json
        Returns:
            LabelGenerator
        """

        warnings.warn(
            "You are currently utilizing COCOconverter for this action, which will be deprecated in a later release.",
            DeprecationWarning,
            stacklevel=2,
        )

        image_root = validate_path(image_root, "image_root")
        mask_root = validate_path(mask_root, "mask_root")
        objs = CocoPanopticDataset(**json_data)
        gen = objs.to_common(image_root, mask_root)
        return LabelGenerator(data=gen)

    @staticmethod
    def deserialize_instances(
        json_data: Dict[str, Any], image_root: Path
    ) -> LabelGenerator:
        """
        Convert coco object data into the labelbox format (as a LabelGenerator).

        Args:
            json_data: coco object data as a dict
            image_root: Path to local images that are referenced by the coco object json
        Returns:
            LabelGenerator
        """

        warnings.warn(
            "You are currently utilizing COCOconverter for this action, which will be deprecated in a later release.",
            DeprecationWarning,
            stacklevel=2,
        )

        image_root = validate_path(image_root, "image_root")
        objs = CocoInstanceDataset(**json_data)
        gen = objs.to_common(image_root)
        return LabelGenerator(data=gen)
