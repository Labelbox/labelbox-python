from collections import defaultdict
from typing import Any, Callable, Dict, List, Union, Optional, get_args
import warnings

import labelbox
from labelbox.data.annotation_types.data.generic_data_row_data import GenericDataRowData
from labelbox.data.annotation_types.data.tiled_image import TiledImageData
from labelbox.schema import ontology
from .annotation import ClassificationAnnotation, ObjectAnnotation
from .relationship import RelationshipAnnotation
from .llm_prompt_response.prompt import PromptClassificationAnnotation
from .classification import ClassificationAnswer
from .data import AudioData, ConversationData, DicomData, DocumentData, HTMLData, ImageData, TextData, VideoData, LlmPromptCreationData, LlmPromptResponseCreationData, LlmResponseCreationData
from .geometry import Mask
from .metrics import ScalarMetric, ConfusionMatrixMetric
from .types import Cuid
from .video import VideoClassificationAnnotation
from .video import VideoObjectAnnotation, VideoMaskAnnotation
from ..ontology import get_feature_schema_lookup
from pydantic import BaseModel, field_validator, model_serializer
from labelbox.pydantic_serializers import _feature_serializer

DataType = Union[VideoData, ImageData, TextData, TiledImageData, AudioData,
                 ConversationData, DicomData, DocumentData, HTMLData,
                 LlmPromptCreationData, LlmPromptResponseCreationData,
                 LlmResponseCreationData, GenericDataRowData]


class Label(BaseModel):
    """Container for holding data and annotations

    >>> Label(
    >>>    data = {'global_key': 'my-data-row-key'} # also accepts uid, external_id as keys
    >>>    annotations = [
    >>>        ObjectAnnotation(
    >>>            value = Point(x = 10, y = 10),
    >>>            name = "target"
    >>>        )
    >>>     ]
    >>>  )

    Args:
        uid: Optional Label Id in Labelbox
        data: Data of Label, Image, Video, Text or dict with a single key uid | global_key | external_id. 
            Note use of classes as data is deprecated. Use GenericDataRowData or dict with a single key instead.
        annotations: List of Annotations in the label
        extra: additional context
    """
    uid: Optional[Cuid] = None
    data: DataType
    annotations: List[Union[ClassificationAnnotation, ObjectAnnotation,
                            VideoMaskAnnotation, ScalarMetric,
                            ConfusionMatrixMetric, RelationshipAnnotation,
                            PromptClassificationAnnotation]] = []
    extra: Dict[str, Any] = {}
    is_benchmark_reference: Optional[bool] = False

    @field_validator("data", mode="before")
    def validate_data(cls, data):
        if isinstance(data, Dict):
            return GenericDataRowData(**data)
        elif isinstance(data, GenericDataRowData):
            return data
        else:
            warnings.warn(
                f"Using {type(data).__name__} class for label.data is deprecated. "
                "Use a dict or an instance of GenericDataRowData instead.")
        return data

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
        warnings.warn("This method is deprecated and will be "
                      "removed in a future release. Feature schema ids"
                      " are no longer required for importing.")
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

    @field_validator("annotations", mode="before")
    def validate_union(cls, value):
        supported = tuple([
            field
            for field in get_args(get_args(cls.model_fields['annotations'].annotation)[0])
        ])
        if not isinstance(value, list):
            raise TypeError(f"Annotations must be a list. Found {type(value)}")
        prompt_count = 0
        for v in value:
            if not isinstance(v, supported):
                raise TypeError(
                    f"Annotations should be a list containing the following classes : {supported}. Found {type(v)}"
                )
            # Validates only one prompt annotation is included
            if isinstance(v, PromptClassificationAnnotation):
                prompt_count += 1
                if prompt_count > 1:
                    raise TypeError(
                        f"Only one prompt annotation is allowed per label")
        return value
