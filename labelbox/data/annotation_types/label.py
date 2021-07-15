from labelbox.data.annotation_types.ner import TextEntity
from labelbox.data.annotation_types.geometry import Geometry
from labelbox.data.annotation_types.classification.classification import Classification, ClassificationAnswer, Radio, Text
from labelbox.data.annotation_types.geometry.mask import Mask
from typing import Union, List, Dict, Any

from labelbox.schema.ontology import Classification as OClassification
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
    extra: Dict[str, Any] = {}

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

        def assign_classification_schema_ids(annotation, answer, tools):
            tool = tools.get(annotation.display_name)
            if annotation.schema_id is None:
                if tool is None:
                    raise ValueError(
                        f"No classification matches display name {annotation.display_name}. "
                        f"Must be one of {list(tools.keys())}.")
                annotation.schema_id = tool.feature_schema_id

            options = {option.value: option for option in tool.options}
            answers = None

            if isinstance(answer, ClassificationAnswer):
                answers = [answer]
            elif isinstance(answer, list):
                if not isinstance(answer[0], ClassificationAnswer):
                    raise TypeError("Unexpected type found.")
                answers = answer
            else:
                if not isinstance(answer, str):
                    raise TypeError(
                        f"Found unexpected answer type : {type(answer)}."
                        "Expected `ClassificationAnswer`, `list`, or `str`")

            if answers is not None:
                for answer in answers:
                    option = options.get(answer.display_name)
                    if option is None:
                        raise ValueError(
                            f"No option matches display name {answer.display_name}. "
                            f"Must be one of {list(options.keys())}.")
                    answer.schema_id = option.feature_schema_id

                    subclass_options = {
                        option.instructions if type(option) is OClassification
                        else option.value: option for option in option.options
                    }

                    for subclass in annotation.classifications:
                        assign_classification_schema_ids(
                            subclass, subclass.value.answer, subclass_options)

        for annotation in self.annotations:
            if isinstance(annotation.value, Classification):
                assign_classification_schema_ids(
                    annotation, annotation.value.value.answer, {
                        tool.name: tool
                        for tool in ontology_builder.classifications
                    })
            elif isinstance(annotation.value, (Geometry, TextEntity)):
                tools = {tool.name: tool for tool in ontology_builder.tools}
                tool = tools.get(annotation.display_name)
                if annotation.schema_id is None:
                    if tool is None:
                        raise ValueError(
                            f"No tool matches display name {annotation.display_name}. "
                            f"Must be one of {list(tools.keys())}.")
                    annotation.schema_id = tool.feature_schema_id
                for classification in annotation.classifications:
                    assign_classification_schema_ids(
                        classification, classification.value.answer,
                        {tool.name: tool for tool in tool.classifications})
