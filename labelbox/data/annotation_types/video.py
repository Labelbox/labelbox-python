from enum import Enum
from typing import List, Optional, Tuple

from labelbox import pydantic_compat
from labelbox.data.annotation_types.annotation import ClassificationAnnotation, ObjectAnnotation

from labelbox.data.annotation_types.annotation import ClassificationAnnotation, ObjectAnnotation
from labelbox.data.annotation_types.feature import FeatureSchema
from labelbox.data.mixins import ConfidenceNotSupportedMixin, CustomMetricsNotSupportedMixin
from labelbox.utils import _CamelCaseMixin, is_valid_uri


class VideoClassificationAnnotation(ClassificationAnnotation):
    """Video classification
    Args:
        name (Optional[str])
        feature_schema_id (Optional[Cuid])
        value (Union[Text, Checklist, Radio, Dropdown])
        frame (int): The frame index that this annotation corresponds to
        segment_id (Optional[Int]): Index of video segment this annotation belongs to
        extra (Dict[str, Any])
    """
    frame: int
    segment_index: Optional[int] = None


class VideoObjectAnnotation(ObjectAnnotation, ConfidenceNotSupportedMixin,
                            CustomMetricsNotSupportedMixin):
    """Video object annotation
    >>> VideoObjectAnnotation(
    >>>     keyframe=True,
    >>>     frame=10,
    >>>     value=Rectangle(
    >>>        start=Point(x=0, y=0),
    >>>        end=Point(x=1, y=1)
    >>>     ),
    >>>     feature_schema_id="my-feature-schema-id"
    >>> )
    Args:
        name (Optional[str])
        feature_schema_id (Optional[Cuid])
        value (Geometry)
        frame (Int): The frame index that this annotation corresponds to
        keyframe (bool): Whether or not this annotation was a human generated or interpolated annotation
        segment_id (Optional[Int]): Index of video segment this annotation belongs to
        classifications (List[ClassificationAnnotation]) = []
        extra (Dict[str, Any])
    """
    frame: int
    keyframe: bool
    segment_index: Optional[int] = None


class GroupKey(Enum):
    """Group key for DICOM annotations
    """
    AXIAL = "axial"
    SAGITTAL = "sagittal"
    CORONAL = "coronal"


class DICOMObjectAnnotation(VideoObjectAnnotation):
    """DICOM object annotation
    >>> DICOMObjectAnnotation(
    >>>     name="dicom_polyline",
    >>>     frame=2,
    >>>     value=lb_types.Line(points = [
    >>>         lb_types.Point(x=680, y=100),
    >>>         lb_types.Point(x=100, y=190),
    >>>         lb_types.Point(x=190, y=220)
    >>>     ]),
    >>>     segment_index=0,
    >>>     keyframe=True,
    >>>     Group_key=GroupKey.AXIAL
    >>> )
    Args:
        name (Optional[str])
        feature_schema_id (Optional[Cuid])
        value (Geometry)
        group_key (GroupKey)
        frame (Int): The frame index that this annotation corresponds to
        keyframe (bool): Whether or not this annotation was a human generated or interpolated annotation
        segment_id (Optional[Int]): Index of video segment this annotation belongs to
        classifications (List[ClassificationAnnotation]) = []
        extra (Dict[str, Any])
    """
    group_key: GroupKey


class MaskFrame(_CamelCaseMixin, pydantic_compat.BaseModel):
    index: int
    instance_uri: Optional[str] = None
    im_bytes: Optional[bytes] = None

    @pydantic_compat.root_validator()
    def validate_args(cls, values):
        im_bytes = values.get("im_bytes")
        instance_uri = values.get("instance_uri")

        if im_bytes == instance_uri == None:
            raise ValueError("One of `instance_uri`, `im_bytes` required.")
        return values

    @pydantic_compat.validator("instance_uri")
    def validate_uri(cls, v):
        if not is_valid_uri(v):
            raise ValueError(f"{v} is not a valid uri")
        return v


class MaskInstance(_CamelCaseMixin, FeatureSchema):
    color_rgb: Tuple[int, int, int]
    name: str


class VideoMaskAnnotation(pydantic_compat.BaseModel):
    """Video mask annotation
       >>> VideoMaskAnnotation(
       >>>     frames=[
       >>>         MaskFrame(index=1, instance_uri='https://storage.labelbox.com/cjhfn5y6s0pk507024nz1ocys%2F1d60856c-59b7-3060-2754-83f7e93e0d01-1?Expires=1666901963361&KeyName=labelbox-assets-key-3&Signature=t-2s2DB4YjFuWEFak0wxYqfBfZA'),
       >>>         MaskFrame(index=5, instance_uri='https://storage.labelbox.com/cjhfn5y6s0pk507024nz1ocys1%2F1d60856c-59b7-3060-2754-83f7e93e0d01-1?Expires=1666901963361&KeyName=labelbox-assets-key-3&Signature=t-2s2DB4YjFuWEFak0wxYqfBfZA'),
       >>>     ],
       >>>     instances=[
       >>>         MaskInstance(color_rgb=(0, 0, 255), name="mask1"),
       >>>         MaskInstance(color_rgb=(0, 255, 0), name="mask2"),
       >>>         MaskInstance(color_rgb=(255, 0, 0), name="mask3")
       >>>     ]
       >>> )
    """
    frames: List[MaskFrame]
    instances: List[MaskInstance]


class DICOMMaskAnnotation(VideoMaskAnnotation):
    """DICOM mask annotation
       >>> DICOMMaskAnnotation(
       >>>     name="dicom_mask",
       >>>     group_key=GroupKey.AXIAL,
       >>>     frames=[
       >>>         MaskFrame(index=1, instance_uri='https://storage.labelbox.com/cjhfn5y6s0pk507024nz1ocys%2F1d60856c-59b7-3060-2754-83f7e93e0d01-1?Expires=1666901963361&KeyName=labelbox-assets-key-3&Signature=t-2s2DB4YjFuWEFak0wxYqfBfZA'),
       >>>         MaskFrame(index=5, instance_uri='https://storage.labelbox.com/cjhfn5y6s0pk507024nz1ocys1%2F1d60856c-59b7-3060-2754-83f7e93e0d01-1?Expires=1666901963361&KeyName=labelbox-assets-key-3&Signature=t-2s2DB4YjFuWEFak0wxYqfBfZA'),
       >>>     ],
       >>>     instances=[
       >>>         MaskInstance(color_rgb=(0, 0, 255), name="mask1"),
       >>>         MaskInstance(color_rgb=(0, 255, 0), name="mask2"),
       >>>         MaskInstance(color_rgb=(255, 0, 0), name="mask3")
       >>>     ]
       >>> )
    """
    group_key: GroupKey
