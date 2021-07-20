from typing import Any, Dict, List, Union

from labelbox.data.annotation_types.annotation import (
    AnnotationType, ClassificationAnnotation, ObjectAnnotation,
    VideoAnnotationType)
from labelbox.data.annotation_types.classification.classification import \
    ClassificationAnswer
from labelbox.data.annotation_types.data.raster import RasterData
from labelbox.data.annotation_types.data.text import TextData
from labelbox.data.annotation_types.data.video import VideoData
from labelbox.data.annotation_types.geometry.mask import Mask
from labelbox.data.annotation_types.metrics import Metric
from labelbox.schema.ontology import Classification as OClassification
from labelbox.schema.ontology import Option
from pydantic import BaseModel


class Label(BaseModel):
    data: Union[VideoData, RasterData, TextData]
    annotations: List[Union[AnnotationType, VideoAnnotationType, Metric]] = []
    extra: Dict[str, Any] = {}

    def add_url_to_data(self, signer):
        """
        Only creates a url if one doesn't exist
        """
        self.data.create_url(signer)
        return self

    def add_url_to_masks(self, signer):
        masks = []
        for annotation in self.annotations:
            # Allows us to upload shared masks once
            if isinstance(annotation.value, Mask):
                if annotation.value.mask not in masks:
                    masks.append(annotation.value.mask)
        for mask in masks:
            mask.create_url(signer)
        return self

    def create_data_row(self, dataset, signer):
        args = {
            'row_data' : self.add_url_to_data(signer)
        }
        if self.data.external_id is not None:
            args.update({
                'external'
            })
        data_row = dataset.create_data_row(**args)
        self.data.uid = data_row.uid
        self.data.external_id = data_row.external_id
        return self

    def get_feature_schema_lookup(self, ontology_builder):
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

    def assign_schema_ids(self, ontology_builder):
        """
        Classifications get flattened when labeling.
        """

        def assign_or_raise(annotation, lookup):
            if annotation.schema_id is not None:
                return

            feature_schema_id = lookup.get(annotation.display_name)
            if feature_schema_id is None:
                raise ValueError(
                    f"No tool matches display name {annotation.display_name}. "
                    f"Must be one of {list(lookup.keys())}.")
            annotation.schema_id = feature_schema_id

        def assign_option(classification, lookup):
            if isinstance(classification.value.answer, str):
                pass
            elif isinstance(classification.value.answer, ClassificationAnswer):
                assign_or_raise(classification.value.answer, lookup)
            elif isinstance(classification.value.answer, list):
                for answer in classification.value.answer:
                    assign_or_raise(answer, lookup)
            else:
                raise TypeError(
                    f"Unexpected type for answer found. {type(classification.value.answer)}"
                )

        tool_lookup, classification_lookup = self.get_feature_schema_lookup(
            ontology_builder)
        for annotation in self.annotations:
            if isinstance(annotation, ClassificationAnnotation):
                assign_or_raise(annotation, classification_lookup)
                assign_option(annotation, classification_lookup)
            elif isinstance(annotation, ObjectAnnotation):
                assign_or_raise(annotation, tool_lookup)
                for classification in annotation.classifications:
                    assign_or_raise(classification, classification_lookup)
                    assign_option(classification, classification_lookup)
            else:
                raise TypeError(
                    f"Unexpected type found for annotation. {type(annotation)}")
        return self
