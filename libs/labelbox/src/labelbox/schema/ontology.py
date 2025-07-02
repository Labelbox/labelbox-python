# type: ignore

import colorsys
import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from lbox.exceptions import InconsistentOntologyException

from labelbox.orm.db_object import DbObject
from labelbox.orm.model import Field, Relationship
from labelbox.schema.tool_building.classification import (
    Classification,
    PromptResponseClassification,
)
from labelbox.schema.tool_building.fact_checking_tool import (
    FactCheckingTool,
)
from labelbox.schema.tool_building.prompt_issue_tool import PromptIssueTool
from labelbox.schema.tool_building.step_reasoning_tool import (
    StepReasoningTool,
)
from labelbox.schema.tool_building.tool_type import ToolType
from labelbox.schema.tool_building.tool_type_mapping import (
    map_tool_type_to_tool_cls,
)
from labelbox.schema.tool_building.types import (
    FeatureSchemaAttribute,
    FeatureSchemaAttributes,
)
import warnings
from labelbox.schema.project import MediaType


class DeleteFeatureFromOntologyResult:
    archived: bool
    deleted: bool

    def __str__(self):
        return "<%s %s>" % (
            self.__class__.__name__.split(".")[-1],
            json.dumps(self.__dict__),
        )


class FeatureSchema(DbObject):
    name = Field.String("name")
    color = Field.String("name")
    normalized = Field.Json("normalized")


@dataclass
class Tool:
    """
    A tool to be added to a Project's ontology. The tool is
    dependent on the Tool Type.

    To instantiate, the "tool" and "name" parameters must
    be passed in.

    The "classifications" parameter holds a list of Classification objects.
    This can be used to add nested classifications to a tool.

    Example(s):
        tool = Tool(
            tool = Tool.Type.LINE,
            name = "Tool example")
        classification = Classification(
            class_type = Classification.Type.TEXT,
            instructions = "Classification Example")
        tool.add_classification(classification)

    Attributes:
        tool: (Tool.Type)
        name: (str)
        required: (bool)
        color: (str)
        classifications: (list)
        schema_id: (str)
        feature_schema_id: (str)
        attributes: (list)
    """

    class Type(Enum):
        POLYGON = "polygon"
        SEGMENTATION = "superpixel"
        RASTER_SEGMENTATION = "raster-segmentation"
        POINT = "point"
        BBOX = "rectangle"
        LINE = "line"
        NER = "named-entity"
        RELATIONSHIP = "edge"
        MESSAGE_SINGLE_SELECTION = "message-single-selection"
        MESSAGE_MULTI_SELECTION = "message-multi-selection"
        MESSAGE_RANKING = "message-ranking"

    tool: Type
    name: str
    required: bool = False
    color: Optional[str] = None
    classifications: List[Classification] = field(default_factory=list)
    schema_id: Optional[str] = None
    feature_schema_id: Optional[str] = None
    attributes: Optional[FeatureSchemaAttributes] = None

    def __post_init__(self):
        if self.attributes is not None:
            warnings.warn(
                "The attributes for Tools are in beta. The attribute name and signature may change in the future."
            )

    @classmethod
    def from_dict(cls, dictionary: Dict[str, Any]) -> Dict[str, Any]:
        return cls(
            name=dictionary["name"],
            schema_id=dictionary.get("schemaNodeId", None),
            feature_schema_id=dictionary.get("featureSchemaId", None),
            required=dictionary.get("required", False),
            tool=Tool.Type(dictionary["tool"]),
            classifications=[
                Classification.from_dict(c)
                for c in dictionary["classifications"]
            ],
            color=dictionary["color"],
            attributes=[
                FeatureSchemaAttribute.from_dict(attr)
                for attr in dictionary.get("attributes", []) or []
            ]
            if dictionary.get("attributes")
            else None,
        )

    def asdict(self) -> Dict[str, Any]:
        return {
            "tool": self.tool.value,
            "name": self.name,
            "required": self.required,
            "color": self.color,
            "classifications": [
                c.asdict(is_subclass=True) for c in self.classifications
            ],
            "schemaNodeId": self.schema_id,
            "featureSchemaId": self.feature_schema_id,
            "attributes": [a.asdict() for a in self.attributes]
            if self.attributes is not None
            else None,
        }

    def add_classification(self, classification: Classification) -> None:
        if classification.name in (c.name for c in self.classifications):
            raise InconsistentOntologyException(
                f"Duplicate nested classification '{classification.name}' "
                f"for tool '{self.name}'"
            )
        self.classifications.append(classification)


"""
The following 2 functions help to bridge the gap between the step reasoning all other tool ontologies.
"""


def tool_cls_from_type(tool_type: str):
    tool_cls = map_tool_type_to_tool_cls(tool_type)
    if tool_cls is not None:
        return tool_cls
    if tool_type == Tool.Type.RELATIONSHIP:
        return RelationshipTool
    return Tool


def tool_type_cls_from_type(tool_type: str):
    if ToolType.valid(tool_type):
        return ToolType
    return Tool.Type


class Ontology(DbObject):
    """An ontology specifies which tools and classifications are available
    to a project. This is read only for now.
    Attributes:
        name (str)
        description (str)
        updated_at (datetime)
        created_at (datetime)
        normalized (json)
        object_schema_count (int)
        classification_schema_count (int)
        projects (Relationship): `ToMany` relationship to Project
        created_by (Relationship): `ToOne` relationship to User
    """

    name = Field.String("name")
    description = Field.String("description")
    updated_at = Field.DateTime("updated_at")
    created_at = Field.DateTime("created_at")
    normalized = Field.Json("normalized")
    object_schema_count = Field.Int("object_schema_count")
    classification_schema_count = Field.Int("classification_schema_count")
    media_type = Field.Enum(MediaType, "media_type", "mediaType")

    projects = Relationship.ToMany("Project", True)
    created_by = Relationship.ToOne("User", False, "created_by")

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._tools: Optional[List[Tool]] = None
        self._classifications: Optional[
            Union[List[Classification], List[PromptResponseClassification]]
        ] = None

    def tools(self) -> List[Tool]:
        """Get list of tools (AKA objects) in an Ontology."""
        if self._tools is None:
            self._tools = [
                tool_cls_from_type(tool["tool"]).from_dict(tool)
                for tool in self.normalized["tools"]
            ]
        return self._tools

    def classifications(
        self,
    ) -> List[Union[Classification, PromptResponseClassification]]:
        """Get list of classifications in an Ontology."""
        if self._classifications is None:
            self._classifications = []
            for classification in self.normalized["classifications"]:
                if (
                    "type" in classification
                    and classification["type"]
                    in PromptResponseClassification.Type._value2member_map_.keys()
                ):
                    self._classifications.append(
                        PromptResponseClassification.from_dict(classification)
                    )
                else:
                    self._classifications.append(
                        Classification.from_dict(classification)
                    )
        return self._classifications


@dataclass
class OntologyBuilder:
    """
    A class to help create an ontology for a Project. This should be used
    for making Project ontologies from scratch. OntologyBuilder can also
    pull from an already existing Project's ontology.

    There are no required instantiation arguments.

    To create an ontology, use the asdict() method after fully building your
    ontology within this class, and inserting it into client.create_ontology() as the
    "normalized" parameter.

    Example:
        >>> builder = OntologyBuilder()
        >>> ...
        >>> ontology = client.create_ontology(
        >>>    "Ontology from new features",
        >>>    ontology_builder.asdict(),
        >>>    media_type=lb.MediaType.Image,
        >>> )
        >>> project.connect_ontology(ontology)

    attributes:
        tools: (list)
        classifications: (list)


    """

    tools: List[
        Union[Tool, StepReasoningTool, FactCheckingTool, PromptIssueTool]
    ] = field(default_factory=list)
    classifications: List[
        Union[Classification, PromptResponseClassification]
    ] = field(default_factory=list)

    @classmethod
    def from_dict(cls, dictionary: Dict[str, Any]) -> Dict[str, Any]:
        classifications = []
        for c in dictionary["classifications"]:
            if (
                "type" in c
                and c["type"]
                in PromptResponseClassification.Type._value2member_map_.keys()
            ):
                classifications.append(
                    PromptResponseClassification.from_dict(c)
                )
            else:
                classifications.append(Classification.from_dict(c))
        return cls(
            tools=[Tool.from_dict(t) for t in dictionary["tools"]],
            classifications=classifications,
        )

    def asdict(self) -> Dict[str, Any]:
        self._update_colors()
        classifications = []
        prompts = 0
        for c in self.classifications:
            if (
                hasattr(c, "class_type")
                and c.class_type in PromptResponseClassification.Type
            ):
                if c.class_type == PromptResponseClassification.Type.PROMPT:
                    prompts += 1
                    if prompts > 1:
                        raise ValueError(
                            "Only one prompt is allowed per ontology"
                        )
                classifications.append(PromptResponseClassification.asdict(c))
            else:
                classifications.append(Classification.asdict(c))
        return {
            "tools": [t.asdict() for t in self.tools],
            "classifications": classifications,
        }

    def _update_colors(self):
        num_tools = len(self.tools)

        for index in range(num_tools):
            hsv_color = (index * 1 / num_tools, 1, 1)
            rgb_color = tuple(
                int(255 * x) for x in colorsys.hsv_to_rgb(*hsv_color)
            )
            if self.tools[index].color is None:
                self.tools[index].color = "#%02x%02x%02x" % rgb_color

    @classmethod
    def from_project(cls, project: "project.Project") -> "OntologyBuilder":
        ontology = project.ontology().normalized
        return cls.from_dict(ontology)

    @classmethod
    def from_ontology(cls, ontology: Ontology) -> "OntologyBuilder":
        return cls.from_dict(ontology.normalized)

    def add_tool(self, tool: Tool) -> None:
        if tool.name in (t.name for t in self.tools):
            raise InconsistentOntologyException(
                f"Duplicate tool name '{tool.name}'. "
            )
        self.tools.append(tool)

    def add_classification(
        self,
        classification: Union[Classification, PromptResponseClassification],
    ) -> None:
        if classification.name in (c.name for c in self.classifications):
            raise InconsistentOntologyException(
                f"Duplicate classification name '{classification.name}'. "
            )
        self.classifications.append(classification)
