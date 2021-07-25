from typing import Any, Dict, List, Tuple, Union, Callable

from pydantic import BaseModel

from labelbox import Classification as OClassification, OntologyBuilder, Option
from labelbox.orm.model import Entity
from .classification import ClassificationAnswer
from .data import VideoData, TextData, RasterData
from .geometry.mask import Mask
from .metrics import Metric
from .annotation import (ClassificationAnnotation, ObjectAnnotation,
                         VideoClassificationAnnotation, VideoObjectAnnotation)

from pydantic import validator


class Label(BaseModel):
    data: Union[VideoData, RasterData, TextData]
    annotations: List[Union[ClassificationAnnotation, ObjectAnnotation,
                            VideoObjectAnnotation,
                            VideoClassificationAnnotation, Metric]] = []
    extra: Dict[str, Any] = {}

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
        Multiple masks can reference the same RasterData mask so this makes sure we only upload that url once.
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
                if annotation.value.mask not in masks:
                    masks.append(annotation.value.mask)
        for mask in masks:
            mask.create_url(signer)
        return self

    def create_data_row(self, dataset: "Entity.Dataset",
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

    def assign_schema_ids(self, ontology_builder: OntologyBuilder) -> "Label":
        """
        Adds schema ids to all FeatureSchema objects in the Labels.
        This is necessary for MAL.

        Args:
            ontology_builder: The ontology that matches the feature names assigned to objects in this dataset
        Returns:
            Label. useful for chaining these modifying functions
        """
        tool_lookup, classification_lookup = self._get_feature_schema_lookup(
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

    def _get_feature_schema_lookup(
        self, ontology_builder: OntologyBuilder
    ) -> Tuple[Dict[str, str], Dict[str, str]]:
        tool_lookup = {}
        classification_lookup = {}

        def flatten_classification(classifications):
            for classification in classifications:
                if isinstance(classification, OClassification):
                    classification_lookup[
                        classification.
                        instructions] = classification.feature_schema_id
                elif isinstance(classification, Option):
                    classification_lookup[
                        classification.value] = classification.feature_schema_id
                else:
                    raise TypeError(
                        f"Unexpected type found in ontology. `{type(classification)}`"
                    )
                flatten_classification(classification.options)

        for tool in ontology_builder.tools:
            tool_lookup[tool.name] = tool.feature_schema_id
            flatten_classification(tool.classifications)
        flatten_classification(ontology_builder.classifications)
        return tool_lookup, classification_lookup

    def _assign_or_raise(self, annotation, lookup: Dict[str, str]) -> None:
        if annotation.schema_id is not None:
            return

        feature_schema_id = lookup.get(annotation.name)
        if feature_schema_id is None:
            raise ValueError(f"No tool matches display name {annotation.name}. "
                             f"Must be one of {list(lookup.keys())}.")
        annotation.schema_id = feature_schema_id

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
