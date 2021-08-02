# Mapping can be used to select classes as instsance or segmentation
# By default polygon will be instance and segmentation will be semantic

# Will use subclasses too..
# checklist and radio will be turned into underscore delimitated names

from labelbox.data.serialization.coco.instance_dataset import CocoInstanceDataset
from labelbox.data.serialization.coco.panoptic_dataset import CocoPanopticDataset


class COCOConverter:
    """
    Note that this class is only compatible with image data.. it will ignore other data types.
    # TODO: Filter out video annotations..
    """

    def serialize_to_object_detection(data):
        im_root = "/Users/matthewsokoloff/Projects/labelbox-python/explore/images/val2017"
        labels = COCOConverter.deserialize_instance(data, image_root=im_root)
        return CocoInstanceDataset.from_common(labels=labels,
                                               image_root=im_root).dict()

    def serialize_to_panoptic(data):
        #im_root = "/Users/matthewsokoloff/Projects/labelbox-python/explore/images/val2017"
        #labels = COCOConverter.deserialize_panoptic(data, image_root = im_root, seg_root = "/Users/matthewsokoloff/Projects/labelbox-python/explore/2017_panoptic/imq/panoptic_val2017")
        im_root = "/Users/matthewsokoloff/Projects/labelbox-python/explore/images/val2017"
        labels = COCOConverter.deserialize_instance(data, image_root=im_root)
        res = CocoPanopticDataset.from_common(
            labels=labels,
            image_root=im_root,
            seg_root=
            "/Users/matthewsokoloff/Projects/labelbox-python/explore/images/masks"
        )
        return res.dict()

    @classmethod
    def deserialize_panoptic(
        cls,
        data,
        image_root="/Users/matthewsokoloff/Projects/labelbox-python/explore/images/val2017",
        seg_root="/Users/matthewsokoloff/Projects/labelbox-python/explore/2017_panoptic/imq/panoptic_val2017"
    ):
        objs = CocoPanopticDataset(**data)
        gen = objs.to_common(image_root, seg_root)
        return gen

    @classmethod
    def deserialize_instance(
        cls,
        data,
        image_root="/Users/matthewsokoloff/Projects/labelbox-python/explore/images/val2017"
    ):
        objs = CocoInstanceDataset(**data)
        gen = objs.to_common(image_root)
        return gen
