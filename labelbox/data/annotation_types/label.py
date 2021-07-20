from typing import Any, Dict, List, Tuple, Union, Callable

from pydantic import BaseModel

from labelbox.schema.ontology import Classification as OClassification, OntologyBuilder, Option
from labelbox.orm.model import Entity
from .classification import ClassificationAnswer
from .data import VideoData, TextData, RasterData
from .geometry.mask import Mask
from .metrics import Metric
from .annotation import (AnnotationType, ClassificationAnnotation,
                         ObjectAnnotation, VideoAnnotationType)


class Label(BaseModel):
    data: Union[VideoData, RasterData, TextData]
    annotations: List[Union[AnnotationType, VideoAnnotationType, Metric]] = []
    extra: Dict[str, Any] = {}

    def add_url_to_data(self, signer) -> "Label":
        """
        Only creates a url if one doesn't exist
        """
        self.data.create_url(signer)
        return self

    def add_url_to_masks(self, signer) -> "Label":
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
        Only overwrites if necessary
        """
        args = {'row_data': self.add_url_to_data(signer)}
        if self.data.external_id is not None:
            args.update({'external_id': self.data.external_id})

        if self.data.uid is None:
            data_row = dataset.create_data_row(**args)
            self.data.uid = data_row.uid
            self.data.external_id = data_row.external_id
        return self

    def assign_schema_ids(self, ontology_builder: OntologyBuilder) -> "Label":
        """
        Classifications get flattened when labeling.
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

        feature_schema_id = lookup.get(annotation.display_name)
        if feature_schema_id is None:
            raise ValueError(
                f"No tool matches display name {annotation.display_name}. "
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
