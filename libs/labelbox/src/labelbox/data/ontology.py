from typing import Dict, List, Tuple, Union

from labelbox.schema import ontology
from .annotation_types import (
    Text,
    Checklist,
    Radio,
    ClassificationAnnotation,
    ObjectAnnotation,
    Mask,
    Point,
    Line,
    Polygon,
    Rectangle,
    TextEntity,
)


def get_feature_schema_lookup(
    ontology_builder: ontology.OntologyBuilder,
) -> Tuple[Dict[str, str], Dict[str, str]]:
    tool_lookup = {}
    classification_lookup = {}

    def flatten_classification(classifications):
        for classification in classifications:
            if classification.feature_schema_id is None:
                raise ValueError(
                    f"feature_schema_id cannot be None for classification `{classification.name}`."
                )
            if isinstance(classification, ontology.Classification):
                classification_lookup[classification.name] = (
                    classification.feature_schema_id
                )
            elif isinstance(classification, ontology.Option):
                classification_lookup[classification.value] = (
                    classification.feature_schema_id
                )
            else:
                raise TypeError(
                    f"Unexpected type found in ontology. `{type(classification)}`"
                )
            flatten_classification(classification.options)

    for tool in ontology_builder.tools:
        if tool.feature_schema_id is None:
            raise ValueError(
                f"feature_schema_id cannot be None for tool `{tool.name}`."
            )
        tool_lookup[tool.name] = tool.feature_schema_id
        flatten_classification(tool.classifications)
    flatten_classification(ontology_builder.classifications)
    return tool_lookup, classification_lookup


def _get_options(
    annotation: ClassificationAnnotation,
    existing_options: List[ontology.Option],
):
    if isinstance(annotation.value, Radio):
        answers = [annotation.value.answer]
    elif isinstance(annotation.value, Text):
        return existing_options
    elif isinstance(annotation.value, (Checklist)):
        answers = annotation.value.answer
    else:
        raise TypeError(
            f"Expected one of Radio, Text, Checklist. Found {type(annotation.value)}"
        )

    option_names = {option.value for option in existing_options}
    for answer in answers:
        if answer.name not in option_names:
            existing_options.append(ontology.Option(value=answer.name))
            option_names.add(answer.name)
    return existing_options


def get_classifications(
    annotations: List[ClassificationAnnotation],
    existing_classifications: List[ontology.Classification],
) -> List[ontology.Classification]:
    existing_classifications = {
        classification.name: classification
        for classification in existing_classifications
    }
    for annotation in annotations:
        # If the classification exists then we just want to add options to it
        classification_feature = existing_classifications.get(annotation.name)
        if classification_feature:
            classification_feature.options = _get_options(
                annotation, classification_feature.options
            )
        elif annotation.name not in existing_classifications:
            existing_classifications[annotation.name] = ontology.Classification(
                class_type=classification_mapping(annotation),
                name=annotation.name,
                options=_get_options(annotation, []),
            )
    return list(existing_classifications.values())


def get_tools(
    annotations: List[ObjectAnnotation],
    existing_tools: List[ontology.Classification],
) -> List[ontology.Tool]:
    existing_tools = {tool.name: tool for tool in existing_tools}
    for annotation in annotations:
        if annotation.name in existing_tools:
            # We just want to update classifications
            existing_tools[
                annotation.name
            ].classifications = get_classifications(
                annotation.classifications,
                existing_tools[annotation.name].classifications,
            )
        else:
            existing_tools[annotation.name] = ontology.Tool(
                tool=tool_mapping(annotation),
                name=annotation.name,
                classifications=get_classifications(
                    annotation.classifications, []
                ),
            )
    return list(existing_tools.values())


def tool_mapping(
    annotation,
) -> Union[Mask, Polygon, Point, Rectangle, Line, TextEntity]:
    tool_types = ontology.Tool.Type
    mapping = {
        Mask: tool_types.SEGMENTATION,
        Polygon: tool_types.POLYGON,
        Point: tool_types.POINT,
        Rectangle: tool_types.BBOX,
        Line: tool_types.LINE,
        TextEntity: tool_types.NER,
    }
    result = mapping.get(type(annotation.value))
    if result is None:
        raise TypeError(
            f"Unexpected type found. {type(annotation.value)}. Expected one of {list(mapping.keys())}"
        )
    return result


def classification_mapping(annotation) -> Union[Text, Checklist, Radio]:
    classification_types = ontology.Classification.Type
    mapping = {
        Text: classification_types.TEXT,
        Checklist: classification_types.CHECKLIST,
        Radio: classification_types.RADIO,
    }
    result = mapping.get(type(annotation.value))
    if result is None:
        raise TypeError(
            f"Unexpected type found. {type(annotation.value)}. Expected one of {list(mapping.keys())}"
        )
    return result
