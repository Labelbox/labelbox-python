import abc
from dataclasses import dataclass, field
from enum import Enum, auto

from typing import Any, Callable, Dict, List, Optional, Union

from labelbox.schema.project import Project
from labelbox.orm import query
from labelbox.orm.db_object import DbObject, Updateable, BulkDeletable
from labelbox.orm.model import Entity, Field, Relationship
from labelbox.utils import snake_case, camel_case
from labelbox.exceptions import InconsistentOntologyException


@dataclass
class Option:
    value: str
    schema_id: Optional[str] = None
    feature_schema_id: Optional[str] = None
    options: List["Classification"] = field(default_factory=list)

    @property
    def label(self):
        return self.value

    @classmethod
    def from_dict(cls, dictionary: Dict[str, Any]):
        return Option(value=dictionary["value"],
                      schema_id=dictionary["schemaNodeId"],
                      feature_schema_id=dictionary["featureSchemaId"],
                      options=[
                          Classification.from_dict(o)
                          for o in dictionary.get("options", [])
                      ])

    def asdict(self) -> Dict[str, Any]:
        return {
            "schemaNodeId": self.schema_id,
            "featureSchemaId": self.feature_schema_id,
            "label": self.label,
            "value": self.value,
            "options": [o.asdict() for o in self.options]
        }

    def add_option(self, option: 'Classification') -> 'Classification':
        if option.instructions in (o.instructions for o in self.options):
            raise InconsistentOntologyException(
                f"Duplicate nested classification '{option.instructions}' "
                f"for option '{self.label}'")
        self.options.append(option)


@dataclass
class Classification:
    class Type(Enum):
        TEXT = "text"
        CHECKLIST = "checklist"
        RADIO = "radio"
        DROPDOWN = "dropdown"

    _REQUIRES_OPTIONS = {Type.CHECKLIST, Type.RADIO, Type.DROPDOWN}

    class_type: Type
    instructions: str
    required: bool = False
    options: List[Option] = field(default_factory=list)
    schema_id: Optional[str] = None
    feature_schema_id: Optional[str] = None

    @property
    def name(self):
        return self.instructions

    @classmethod
    def from_dict(cls, dictionary: Dict[str, Any]):
        return Classification(
            class_type=Classification.Type(dictionary["type"]),
            instructions=dictionary["instructions"],
            required=dictionary["required"],
            options=[Option.from_dict(o) for o in dictionary["options"]],
            schema_id=dictionary["schemaNodeId"],
            feature_schema_id=dictionary["schemaNodeId"])

    def asdict(self) -> Dict[str, Any]:
        if self.class_type in Classification._REQUIRES_OPTIONS \
                and len(self.options) < 1:
            raise InconsistentOntologyException(
                f"Classification '{self.instructions}' requires options.")
        return {
            "type": self.class_type.value,
            "instructions": self.instructions,
            "name": self.name,
            "required": self.required,
            "options": [o.asdict() for o in self.options],
            "schemaNodeId": self.schema_id,
            "featureSchemaId": self.feature_schema_id
        }

    def add_option(self, option: Option):
        if option.value in (o.value for o in self.options):
            raise InconsistentOntologyException(
                f"Duplicate option '{option.value}' "
                f"for classification '{self.name}'.")
        self.options.append(option)


@dataclass
class Tool:
    class Type(Enum):
        POLYGON = "polygon"
        SEGMENTATION = "superpixel"
        POINT = "point"
        BBOX = "rectangle"
        LINE = "line"
        NER = "named-entity"

    tool: Type
    name: str
    required: bool = False
    color: str = "#000000"
    classifications: List[Classification] = field(default_factory=list)
    schema_id: Optional[str] = None
    feature_schema_id: Optional[str] = None

    @classmethod
    def from_dict(cls, dictionary: Dict[str, Any]):
        return Tool(name=dictionary['name'],
                    schema_id=dictionary["schemaNodeId"],
                    feature_schema_id=dictionary["featureSchemaId"],
                    required=dictionary["required"],
                    tool=Tool.Type(dictionary["tool"]),
                    classifications=[
                        Classification.from_dict(c)
                        for c in dictionary["classifications"]
                    ],
                    color=dictionary["color"])

    def asdict(self) -> Dict[str, Any]:
        return {
            "tool": self.tool.value,
            "name": self.name,
            "required": self.required,
            "color": self.color,
            "classifications": [c.asdict() for c in self.classifications],
            "schemaNodeId": self.schema_id,
            "featureSchemaId": self.feature_schema_id
        }

    def add_classification(self, classification: Classification):
        if classification.instructions in (c.instructions
                                           for c in self.classifications):
            raise InconsistentOntologyException(
                f"Duplicate nested classification '{classification.instructions}' "
                f"for tool '{self.name}'")
        self.classifications.append(classification)


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

    projects = Relationship.ToMany("Project", True)
    created_by = Relationship.ToOne("User", False, "created_by")

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._tools: Optional[List[Tool]] = None
        self._classifications: Optional[List[Classification]] = None

    def tools(self) -> List[Tool]:
        """Get list of tools (AKA objects) in an Ontology."""
        if self._tools is None:
            self._tools = [
                Tool.from_dict(tool) for tool in self.normalized['tools']
            ]
        return self._tools  # type: ignore

    def classifications(self) -> List[Classification]:
        """Get list of classifications in an Ontology."""
        if self._classifications is None:
            self._classifications = [
                Classification.from_dict(classification)
                for classification in self.normalized['classifications']
            ]
        return self._classifications  # type: ignore


def convert_keys(json_dict: Dict[str, Any],
                 converter: Callable) -> Dict[str, Any]:
    if isinstance(json_dict, dict):
        return {
            converter(key): convert_keys(value, converter)
            for key, value in json_dict.items()
        }
    if isinstance(json_dict, list):
        return [convert_keys(ele, converter) for ele in json_dict]
    return json_dict


@dataclass
class OntologyBuilder:

    tools: List[Tool] = field(default_factory=list)
    classifications: List[Classification] = field(default_factory=list)

    @classmethod
    def from_dict(cls, dictionary: Dict[str, Any]):
        return OntologyBuilder(
            tools=[Tool.from_dict(t) for t in dictionary["tools"]],
            classifications=[
                Classification.from_dict(c)
                for c in dictionary["classifications"]
            ])

    def asdict(self):
        return {
            "tools": [t.asdict() for t in self.tools],
            "classifications": [c.asdict() for c in self.classifications]
        }

    @classmethod
    def from_project(cls, project: Project):
        ontology = project.ontology().normalized
        return OntologyBuilder.from_dict(ontology)

    def add_tool(self, tool: Tool) -> Tool:
        if tool.name in (t.name for t in self.tools):
            raise InconsistentOntologyException(
                f"Duplicate tool name '{tool.name}'. ")
        self.tools.append(tool)

    def add_classification(self,
                           classification: Classification) -> Classification:
        if classification.instructions in (c.instructions
                                           for c in self.classifications):
            raise InconsistentOntologyException(
                f"Duplicate classification instructions '{classification.instructions}'. "
            )
        self.classifications.append(classification)
