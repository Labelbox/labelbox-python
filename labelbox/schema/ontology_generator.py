'''
TODO
Option.add_option() currently creates a new Classification object. however, this does not work for certain Classification options.
    Example: 
        Classification.Type.DROPDOWN -> the options for this class_type should only generate more nested dropdowns
            -> Dropdowns are supposed to be removed moving forward, but this is a current problem
            -> This is the most major issue because going to the doubly nested class will break the UI
        Classification.Type.CHECKLIST & Classification.Type.TEXT-> the option cannot have a nested Classification. 
            -> this reflects accurately in the UI without issues, but when you query via graphql, it shows what was input
            -> this is a lesser issue because the UI will not reflect the unavailable fields
    Is there an effective way to enforce limitations on Option.add_option()?
        -> Maybe a way to check if the Option itself has options when adding it to a Classification?
'''

from dataclasses import dataclass, field
from enum import Enum, auto
import os
from typing import List, Optional, Dict

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
    
    def asdict(self) -> Dict[str, str]:
        return {
            "schemaNodeId": self.schema_id,
            "featureSchemaId": self.feature_schema_id,
            "label": self.label,
            "value": self.value,
            "options": [c.asdict() for c in self.options]
        }

    @classmethod
    def from_dict(cls, dictionary: Dict[str,str]):
        return Option(
            value = dictionary["value"],
            schema_id = dictionary["schemaNodeId"],
            feature_schema_id = dictionary["featureSchemaId"],
            options = [Classification.from_dict(nested_class) for nested_class in dictionary.get("options", [])]
        )

    def add_option(self, *args, **kwargs):
        new_option = Classification(*args, **kwargs)
        if new_option.instructions in (c.instructions for c in self.options):
            raise InconsistentOntologyException(f"Duplicate nested classification '{new_option.instructions}' for option '{self.label}'")
        self.options.append(new_option)
        return new_option
    
@dataclass
class Classification:    

    class Type(Enum):
        TEXT = "text"
        CHECKLIST = "checklist"
        RADIO = "radio"
        DROPDOWN = "dropdown"

    _REQUIRES_OPTIONS = set((Type.CHECKLIST, Type.RADIO, Type.DROPDOWN))

    class_type: Type
    instructions: str
    required: bool = False
    options: List[Option] = field(default_factory=list)
    schema_id: Optional[str] = None
    feature_schema_id: Optional[str] = None

    @property
    def name(self):
        return self.instructions

    def asdict(self) -> Dict[str,str]:
        if self.class_type in Classification._REQUIRES_OPTIONS and len(self.options) < 1:
            raise InconsistentOntologyException(f"Classification '{self.instructions}' requires options.")
        return {
            "type": self.class_type.value,
            "instructions": self.instructions,
            "name": self.name,
            "required": self.required,
            "options": [o.asdict() for o in self.options],
            "schemaNodeId": self.schema_id,
            "featureSchemaId": self.feature_schema_id
        }   

    @classmethod
    def from_dict(cls, dictionary: Dict[str,str]): 
        return Classification(
            class_type = Classification.Type(dictionary["type"]),
            instructions = dictionary["instructions"],
            required = dictionary["required"],
            options = [Option.from_dict(o) for o in dictionary["options"]],
            schema_id = dictionary["schemaNodeId"],
            feature_schema_id = dictionary["schemaNodeId"]
        )

    def add_option(self, *args, **kwargs):
        new_option = Option(*args, **kwargs)
        if new_option.value in (o.value for o in self.options):
            raise InconsistentOntologyException(f"Duplicate option '{new_option.value}' for classification '{self.name}'.")
        self.options.append(new_option)
        return new_option

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

    def asdict(self) -> Dict[str,str]:
        return {
            "tool": self.tool.value,
            "name": self.name,
            "required": self.required,
            "color": self.color,
            "classifications": [c.asdict() for c in self.classifications],
            "schemaNodeId": self.schema_id,
            "featureSchemaId": self.feature_schema_id
        }

    @classmethod 
    def from_dict(cls, dictionary: Dict[str,str]):
        return Tool(
            name = dictionary['name'],
            schema_id = dictionary["schemaNodeId"],
            feature_schema_id = dictionary["featureSchemaId"],
            required = dictionary["required"],
            tool = Tool.Type(dictionary["tool"]),   
            classifications = [Classification.from_dict(c) for c in dictionary["classifications"]],
            color = dictionary["color"]
        )

    def add_nested_class(self, *args, **kwargs):
        new_classification = Classification(*args, **kwargs)
        if new_classification.instructions in (c.instructions for c in self.classifications):
            raise InconsistentOntologyException(f"Duplicate nested classification '{new_classification.instructions}' for option '{self.label}'")
        self.classifications.append(new_classification)
        return new_classification        

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

    def add_tool(self, *args, **kwargs) -> Tool:        
        new_tool = Tool(*args, **kwargs)
        if new_tool.name in (t.name for t in self.tools):
            raise InconsistentOntologyException(f"Duplicate tool name '{new_tool.name}'. ")
        self.tools.append(new_tool)
        return new_tool

    def add_classification(self, *args, **kwargs) -> Classification:
        new_classification = Classification(*args, **kwargs)    
        if new_classification.instructions in (c.instructions for c in self.classifications):
            raise InconsistentOntologyException(f"Duplicate classifications instructions '{new_classification.instructions}'. ")
        self.classifications.append(new_classification)
        return new_classification

    def asdict(self):
        all_tools = []
        all_classifications = []

        for tool in self.tools:
            all_tools.append(tool.asdict())

        for classification in self.classifications:   
            all_classifications.append(classification.asdict())

        return {"tools": all_tools, "classifications": all_classifications}

if __name__ == "__main__":
    pass