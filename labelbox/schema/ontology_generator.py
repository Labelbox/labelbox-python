from dataclasses import dataclass, field
from enum import Enum, auto
import os
from typing import List, Optional, Dict, Any

from labelbox import Client, Project, Dataset, LabelingFrontend


class InconsistentOntologyException(Exception):
    pass

@dataclass
class Option:
    value: str    
    schema_id: Optional[str] = None
    feature_schema_id: Optional[str] = None
    options: List["Classification"] = field(default_factory=list)

    @property
    def label(self):
        return self.value
    
    def asdict(self) -> Dict[str, Any]:
        return {
            "schemaNodeId": self.schema_id,
            "featureSchemaId": self.feature_schema_id,
            "label": self.label,
            "value": self.value,
            "options": [o.asdict() for o in self.options]}

    @classmethod
    def from_dict(cls, dictionary: Dict[str,Any]):
        return Option(
            value = dictionary["value"],
            schema_id = dictionary["schemaNodeId"],
            feature_schema_id = dictionary["featureSchemaId"],
            options = [Classification.from_dict(o) 
                       for o in dictionary.get("options", [])])

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

    def asdict(self) -> Dict[str,Any]:
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
            "featureSchemaId": self.feature_schema_id}   

    @classmethod
    def from_dict(cls, dictionary: Dict[str,Any]): 
        return Classification(
            class_type = Classification.Type(dictionary["type"]),
            instructions = dictionary["instructions"],
            required = dictionary["required"],
            options = [Option.from_dict(o) for o in dictionary["options"]],
            schema_id = dictionary["schemaNodeId"],
            feature_schema_id = dictionary["schemaNodeId"])

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

    def asdict(self) -> Dict[str,Any]:
        return {
            "tool": self.tool.value,
            "name": self.name,
            "required": self.required,
            "color": self.color,
            "classifications": [c.asdict() for c in self.classifications],
            "schemaNodeId": self.schema_id,
            "featureSchemaId": self.feature_schema_id}

    @classmethod 
    def from_dict(cls, dictionary: Dict[str,Any]):
        return Tool(
            name = dictionary['name'],
            schema_id = dictionary["schemaNodeId"],
            feature_schema_id = dictionary["featureSchemaId"],
            required = dictionary["required"],
            tool = Tool.Type(dictionary["tool"]), 
            classifications = [Classification.from_dict(c) 
                               for c in dictionary["classifications"]],
            color = dictionary["color"])

    def add_classification(self, classification: Classification):
        if classification.instructions in (c.instructions 
                                           for c in self.classifications):
            raise InconsistentOntologyException(
                f"Duplicate nested classification '{classification.instructions}' "
                f"for tool '{self.name}'")
        self.classifications.append(classification)      

@dataclass
class Ontology:
    
    tools: List[Tool] = field(default_factory=list)
    classifications: List[Classification] = field(default_factory=list)

    @classmethod
    def from_project(cls, project: Project):
        ontology = project.ontology().normalized
        return_ontology = Ontology()

        for tool in ontology["tools"]: 
            return_ontology.tools.append(Tool.from_dict(tool))

        for classification in ontology["classifications"]:
            return_ontology.classifications.append(Classification.from_dict(classification))
 
        return return_ontology

    def add_tool(self, tool: Tool) -> Tool: 
        if tool.name in (t.name for t in self.tools):
            raise InconsistentOntologyException(
                f"Duplicate tool name '{tool.name}'. ")
        self.tools.append(tool)
   
    def add_classification(self, classification: Classification) -> Classification:
        if classification.instructions in (c.instructions 
                                           for c in self.classifications):
            raise InconsistentOntologyException(
                f"Duplicate classification instructions '{classification.instructions}'. ")
        self.classifications.append(classification)

    def asdict(self):
        return {
            "tools": [t.asdict() for t in self.tools],
            "classifications": [c.asdict() for c in self.classifications]}