from labelbox.data.annotation_types.ner import TextEntity
from labelbox.data.annotation_types.geometry import Geometry
from labelbox.data.annotation_types.classification.classification import Classification, ClassificationAnswer
from labelbox.data.annotation_types.geometry.mask import Mask
from typing import Union, List

from labelbox.schema.ontology import OntologyBuilder
from labelbox.data.annotation_types.annotation import Annotation
from labelbox.data.annotation_types.data.raster import RasterData
from labelbox.data.annotation_types.data.text import TextData
from labelbox.data.annotation_types.data.video import VideoData
from labelbox.data.annotation_types.metrics import Metric
from pydantic import BaseModel


class Label(BaseModel):
    # TODO: This sounds too much like the other label we need to rename this...
    data: Union[RasterData, TextData, VideoData]
    annotations: List[Union[Annotation, Metric]] = []

    def create_url_for_data(self, signer):
        return self.data.create_url(signer)

    def create_url_for_masks(self, signer):
        masks = []
        for annotation in self.annotations:
            # Allows us to upload shared masks once
            if isinstance(annotation.value, Mask):
                if annotation.value.mask not in masks:
                    masks.append(annotation.value.mask)
        for mask in masks:
            mask.create_url(signer)

    def create_data_row(self, dataset, signer):
        data_row = dataset.create_data_row(
            row_data=self.create_url_for_data(signer))
        self.data.uid = data_row.uid
        return data_row

    def assign_schema_ids(self, ontology_builder):

        def assign_classification_schema_ids(annotation, tools):
            tool = tools.get(annotation.display_name)
            if annotation.schema_id is None:
                if tool is None:
                    raise ValueError(
                        f"No classification matches display name {annotation.display_name}."
                        f"Must be one of {list(tools.keys())}.")
                annotation.schema_id = tool.feature_schema_id

            options = {option.value: option for option in tool.options}
            answers = None
            if isinstance(annotation.value.answer, ClassificationAnswer):
                answers = [annotation.value.answer]
            elif isinstance(annotation.value.answer, list):
                if not isinstance(annotation.value.answer[0],
                                  ClassificationAnswer):
                    raise TypeError("Unexpected type found.")
                answers = annotation.value.answer
            else:
                # TODO: raise TypeError if not Text
                pass

            # Nested classifications rely on the value picked...
            # But that constraint isn't built into the hierarchy of annotation types.
            # So this will throw an unclear exception.
            # TODO: Handle these excpetions well.
            if answers is not None:
                for answer in answers:
                    # Note that subclasses will overwrite schema ids that already exist...
                    # TODO: Update this to work like top level classifications.
                    option = options.get(answer.display_name)
                    if option is None:
                        raise ValueError(
                            f"No option matches display name {answer.display_name}."
                            f"Must be one of {list(option.keys())}.")
                    answer.schema_id = option.feature_schema_id
                    subclass_options = {
                        option.name: option for option in option.options
                    }
                    for subclass in annotation.classifications:
                        assign_classification_schema_ids(
                            subclass, subclass_options)

        for annotation in self.annotations:
            if isinstance(annotation.value, Classification):
                assign_classification_schema_ids(
                    annotation,
                    {tool.name: tool for tool in ontology_builder.tools})
            elif isinstance(annotation.value, (Geometry, TextEntity)):
                tools = {tool.name: tool for tool in ontology_builder.tools}
                tool = tools.get(annotation.display_name)
                if annotation.schema_id is None:
                    if tool is None:
                        raise ValueError(
                            f"No tool matches display name {annotation.display_name}."
                            f"Must be one of {list(tools.keys())}.")
                    annotation.schema_id = tool.feature_schema_id
                for classification in annotation.classifications:
                    assign_classification_schema_ids(
                        classification,
                        {tool.name: tool for tool in ontology_builder.tools})
