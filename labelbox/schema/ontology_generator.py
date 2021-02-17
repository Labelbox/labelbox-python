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
            options = [Classification.from_dict(o) for o in dictionary.get("options", [])]
        )

    def add_option(self, new_o: 'Classification') -> 'Classification':
        if new_o.instructions in (c.instructions for c in self.options):
            #what is the best way to shorten exceptions?
            raise InconsistentOntologyException(f"Duplicate nested classification '{new_o.instructions}' for option '{self.label}'")
        self.options.append(new_o)
        return new_o
    
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

    def asdict(self) -> Dict[str,str]:
        #unsure how to shorten this specification
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

    def add_option(self, new_o: Option):
        if new_o.value in (o.value for o in self.options):
            raise InconsistentOntologyException(f"Duplicate option '{new_o.value}' for classification '{self.name}'.")
        self.options.append(new_o)
        return new_o

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
            #is there a way to shorten this classifications line at 140?  
            classifications = [Classification.from_dict(c) for c in dictionary["classifications"]],
            color = dictionary["color"]
        )

    def add_nested_class(self, new_c: Classification) -> Classification:
        if new_c.instructions in (c.instructions for c in self.classifications):
            raise InconsistentOntologyException(f"Duplicate nested classification '{new_c.instructions}' for option '{self.label}'")
        self.classifications.append(new_c)
        return new_c        

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

    def add_tool(self, new_tool: Tool) -> Tool:
        if new_tool.name in (t.name for t in self.tools):
            raise InconsistentOntologyException(f"Duplicate tool name '{new_tool.name}'. ")
        self.tools.append(new_tool)
        return new_tool
   
    def add_classification(self, new_c: Classification) -> Classification:
        if new_c.instructions in (c.instructions for c in self.classifications):
            raise InconsistentOntologyException(f"Duplicate classifications instructions '{new_c.instructions}'. ")
        self.classifications.append(new_c)
        return new_c

    def asdict(self):
        return {
            "tools": [t.asdict() for t in self.tools],
            "classifications": [c.asdict() for c in self.classifications]
        }

if __name__ == "__main__":
    pass