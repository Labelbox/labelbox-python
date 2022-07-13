from collections import defaultdict
from typing import Any, Callable, Dict, List, Union, Optional

from pydantic import BaseModel, validator

import labelbox
from labelbox.data.annotation_types.data.tiled_image import TiledImageData
from labelbox.schema import ontology
from .annotation import (ClassificationAnnotation, ObjectAnnotation,
                         VideoClassificationAnnotation, VideoObjectAnnotation)
from .classification import ClassificationAnswer
from .data import VideoData, TextData, ImageData
from .geometry import Mask
from .metrics import ScalarMetric, ConfusionMatrixMetric
from .types import Cuid
from ..ontology import get_feature_schema_lookup


class Label(BaseModel):
    """Container for holding data and annotations

    >>> Label(
    >>>    data = ImageData(url = "http://my-img.jpg"),
    >>>    annotations = [
    >>>        ObjectAnnotation(
    >>>            value = Point(x = 10, y = 10),
    >>>            name = "target"
    >>>        )
    >>>     ]
    >>>  )

    Args:
        uid: Optional Label Id in Labelbox
        data: Data of Label, Image, Video, Text
        annotations: List of Annotations in the label
        extra: additional context
    """
    uid: Optional[Cuid] = None
    data: Union[VideoData, ImageData, TextData, TiledImageData]
    annotations: List[Union[ClassificationAnnotation, ObjectAnnotation,
                            VideoObjectAnnotation,
                            VideoClassificationAnnotation, ScalarMetric,
                            ConfusionMatrixMetric]] = []
    extra: Dict[str, Any] = {}

    def object_annotations(self) -> List[ObjectAnnotation]:
        return self._get_annotations_by_type(ObjectAnnotation)

    def classification_annotations(self) -> List[ClassificationAnnotation]:
        return self._get_annotations_by_type(ClassificationAnnotation)

    def _get_annotations_by_type(self, annotation_type):
        return [
            annot for annot in self.annotations
            if isinstance(annot, annotation_type)
        ]

    def frame_annotations(
        self
    ) -> Dict[str, Union[VideoObjectAnnotation, VideoClassificationAnnotation]]:
        frame_dict = defaultdict(list)
        for annotation in self.annotations:
            if isinstance(
                    annotation,
                (VideoObjectAnnotation, VideoClassificationAnnotation)):
                frame_dict[annotation.frame].append(annotation)
        return frame_dict

    def add_url_to_data(self, signer) -> "Label":
        """
        Creates signed urls for the data
        Only uploads url if one doesn't already exist.

        Args:
            signer: A function that accepts bytes and returns a signed url.
        Returns:
            Label with updated references to new data url
        """
        self.data.create_url(signer)
        return self

    def add_url_to_masks(self, signer) -> "Label":
        """
        Creates signed urls for all masks in the Label.
        Multiple masks can reference the same MaskData mask so this makes sure we only upload that url once.
        Only uploads url if one doesn't already exist.

        Args:
            signer: A function that accepts bytes and returns a signed url.
        Returns:
            Label with updated references to new mask url
        """
        masks = []
        for annotation in self.annotations:
            # Allows us to upload shared masks once
            if isinstance(annotation.value, Mask):
                in_list = False
                for mask in masks:
                    if annotation.value.mask is mask:
                        in_list = True
                if not in_list:
                    masks.append(annotation.value.mask)
        for mask in masks:
            mask.create_url(signer)
        return self

    def create_data_row(self, dataset: "labelbox.Dataset",
                        signer: Callable[[bytes], str]) -> "Label":
        """
        Creates a data row and adds to the given dataset.
        Updates the label's data object to have the same external_id and uid as the data row.

        Args:
            dataset: labelbox dataset object to add the new data row to
            signer: A function that accepts bytes and returns a signed url.
        Returns:
            Label with updated references to new data row
        """
        args = {'row_data': self.data.create_url(signer)}
        if self.data.external_id is not None:
            args.update({'external_id': self.data.external_id})

        if self.data.uid is None:
            data_row = dataset.create_data_row(**args)
            self.data.uid = data_row.uid
            self.data.external_id = data_row.external_id
        return self

    def assign_feature_schema_ids(
            self, ontology_builder: ontology.OntologyBuilder) -> "Label":
        """
        Adds schema ids to all FeatureSchema objects in the Labels.

        Args:
            ontology_builder: The ontology that matches the feature names assigned to objects in this dataset
        Returns:
            Label. useful for chaining these modifying functions

        Note: You can now import annotations using names directly without having to lookup schema_ids
        """
        tool_lookup, classification_lookup = get_feature_schema_lookup(
            ontology_builder)
        for annotation in self.annotations:
            if isinstance(annotation, ClassificationAnnotation):
                self._assign_or_raise(annotation, classification_lookup)
                self._assign_option(annotation, classification_lookup)
            elif isinstance(annotation, ObjectAnnotation):
                self._assign_or_raise(annotation, tool_lookup)
                for classification in annotation.classifications:
                    self._assign_or_raise(classification, classification_lookup)
                    self._assign_option(classification, classification_lookup)
            else:
                raise TypeError(
                    f"Unexpected type found for annotation. {type(annotation)}")
        return self

    def _assign_or_raise(self, annotation, lookup: Dict[str, str]) -> None:
        if annotation.feature_schema_id is not None:
            return

        feature_schema_id = lookup.get(annotation.name)
        if feature_schema_id is None:
            raise ValueError(f"No tool matches name {annotation.name}. "
                             f"Must be one of {list(lookup.keys())}.")
        annotation.feature_schema_id = feature_schema_id

    def _assign_option(self, classification: ClassificationAnnotation,
                       lookup: Dict[str, str]) -> None:
        if isinstance(classification.value.answer, str):
            pass
        elif isinstance(classification.value.answer, ClassificationAnswer):
            self._assign_or_raise(classification.value.answer, lookup)
        elif isinstance(classification.value.answer, list):
            for answer in classification.value.answer:
                self._assign_or_raise(answer, lookup)
        else:
            raise TypeError(
                f"Unexpected type for answer found. {type(classification.value.answer)}"
            )

    @validator("annotations", pre=True)
    def validate_union(cls, value):
        supported = tuple([
            field.type_
            for field in cls.__fields__['annotations'].sub_fields[0].sub_fields
        ])
        if not isinstance(value, list):
            raise TypeError(f"Annotations must be a list. Found {type(value)}")

        for v in value:
            if not isinstance(v, supported):
                raise TypeError(
                    f"Annotations should be a list containing the following classes : {supported}. Found {type(v)}"
                )
        return value
