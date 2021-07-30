


# Mapping can be used to select classes as instsance or segmentation
# By default polygon will be instance and segmentation will be semantic

# Will use subclasses too..
# checklist and radio will be turned into underscore delimitated names



class COCOConverter:
    def serialize_to_object_detection(mapping = None):
        # Polygons and boxes are converted
        # Optionally extract objects

    def serialize_to_panoptic(mapping = None):
        ...
        # coco panoptic assigns each pixel an object
        # Instance segmentation for polygons
        # Semantic segmentation for masks


        # Convert to fpn compatible model with:
        # https://github.com/facebookresearch/detectron2/blob/master/datasets/prepare_panoptic_fpn.py

