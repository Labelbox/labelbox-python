'''
TODO
maybe there should be a way to check if a project has an existing ontology, and that it would overwrite it?
'''

from dataclasses import dataclass, field
from enum import Enum, auto
import os
from typing import List, Optional, Dict

from labelbox import Client, Project, Dataset, LabelingFrontend


class InconsistentOntologyException(Exception):
    pass

class Classification:
    pass

@dataclass
class Option:
    value: str    
    schema_id: Optional[str] = None
    feature_schema_id: Optional[str] = None
    nested_classes: List[Classification] = field(default_factory=list)

    @property
    def label(self):
        return self.value
    
    def to_dict(self,for_different_project=False) -> Dict[str, str]:
        return {
            "schemaNodeId": None if for_different_project else self.schema_id,
            "featureSchemaId": None if for_different_project else self.feature_schema_id,
            "label": self.label,
            "value": self.value,
            "options": [classification.to_dict(for_different_project) for classification in self.nested_classes]
        }

    @classmethod
    def from_dict(cls, dictionary: Dict[str,str]):
        def has_nested_classifications(dictionary: Dict[str,str]):
            return [Classification.from_dict(nested_class) for nested_class in dictionary.get("options", [])]

        return Option(
            value = dictionary["value"],
            schema_id = dictionary["schemaNodeId"],
            feature_schema_id = dictionary["featureSchemaId"],
            nested_classes = has_nested_classifications(dictionary)
        )

    def add_nested_class(self, *args, **kwargs):
        new_classification = Classification(*args, **kwargs)
        if new_classification.instructions in (classification.instructions for classification in self.nested_classes):
            raise InconsistentOntologyException(f"Duplicate nested classification '{new_classification.instructions}' for option '{self.label}'")
        self.nested_classes.append(new_classification)
        return new_classification
    
@dataclass
class Classification:    

    class Type(Enum):
        TEXT = "text"
        CHECKLIST = "checklist"
        RADIO = "radio"
        DROPDOWN = "dropdown"

    class_type: Type
    instructions: str
    required: bool = False
    options: List[Option] = field(default_factory=list)
    schema_id: Optional[str] = None
    feature_schema_id: Optional[str] = None

    @staticmethod
    def requires_options():
         return set((Classification.Type.CHECKLIST, Classification.Type.RADIO, Classification.Type.DROPDOWN))    

    @property
    def name(self):
        return self.instructions

    def to_dict(self, for_different_project=False) -> Dict[str,str]:
        if self.class_type in Classification.requires_options() and len(self.options) < 1:
            raise InconsistentOntologyException(f"Classification '{self.instructions}' requires options.")
        return {
            "type": self.class_type.value,
            "instructions": self.instructions,
            "name": self.name,
            "required": self.required,
            "options": [option.to_dict(for_different_project) for option in self.options],
            "schemaNodeId": None if for_different_project else self.schema_id,
            "featureSchemaId": None if for_different_project else self.feature_schema_id
        }   

    @classmethod
    def from_dict(cls, dictionary: Dict[str,str]): 
        return Classification(
            class_type = Classification.Type(dictionary["type"]),
            instructions = dictionary["instructions"],
            required = dictionary["required"],
            options = [Option.from_dict(option) for option in dictionary["options"]],
            schema_id = dictionary["schemaNodeId"],
            feature_schema_id = dictionary["schemaNodeId"]
        )

    def add_option(self, *args, **kwargs):
        new_option = Option(*args, **kwargs)
        if new_option.value in (option.value for option in self.options):
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

    def to_dict(self,for_different_project=False) -> Dict[str,str]:
        return {
            "tool": self.tool.value,
            "name": self.name,
            "required": self.required,
            "color": self.color,
            "classifications": [classification.to_dict(for_different_project) for classification in self.classifications],
            "schemaNodeId": None if for_different_project else self.schema_id,
            "featureSchemaId": None if for_different_project else self.feature_schema_id
        }

    @classmethod 
    def from_dict(cls, dictionary: Dict[str,str]):
        return Tool(
            name = dictionary['name'],
            schema_id = dictionary["schemaNodeId"],
            feature_schema_id = dictionary["featureSchemaId"],
            required = dictionary["required"],
            tool = Tool.Type(dictionary["tool"]),   
            classifications = [Classification.from_dict(classification) for classification in dictionary["classifications"]],
            color = dictionary["color"]
        )

    def add_nested_class(self, *args, **kwargs):
        new_classification = Classification(*args, **kwargs)
        if new_classification.instructions in (classification.instructions for classification in self.classifications):
            raise InconsistentOntologyException(f"Duplicate nested classification '{new_classification.instructions}' for option '{self.label}'")
        self.classifications.append(new_classification)
        return new_classification        

@dataclass
class Ontology:
    
    tools: List[Tool] = field(default_factory=list)
    classifications: List[Classification] = field(default_factory=list)

    @classmethod
    def from_project(cls, project: Project):
        #TODO: consider if this should take in a Project object, or the project.uid. 
        #if we take in project.uid, we need to then get the project from a client object. 
        ontology = project.ontology().normalized
        return_ontology = Ontology()

        for tool in ontology["tools"]: 
            return_ontology.tools.append(Tool.from_dict(tool))

        for classification in ontology["classifications"]:
            return_ontology.classifications.append(Classification.from_dict(classification))
 
        return return_ontology

    def add_tool(self, *args, **kwargs) -> Tool:        
        new_tool = Tool(*args, **kwargs)
        if new_tool.name in (tool.name for tool in self.tools):
            raise InconsistentOntologyException(f"Duplicate tool name '{new_tool.name}'. ")
        self.tools.append(new_tool)
        return new_tool

    def add_classification(self, *args, **kwargs) -> Classification:
        new_classification = Classification(*args, **kwargs)    
        if new_classification.instructions in (classification.instructions for classification in self.classifications):
            raise InconsistentOntologyException(f"Duplicate classifications instructions '{new_classification.instructions}'. ")
        self.classifications.append(new_classification)
        return new_classification

    def build(self, for_different_project=False):
        all_tools = []
        all_classifications = []

        for tool in self.tools:
            all_tools.append(tool.to_dict(for_different_project))

        for classification in self.classifications:   
            all_classifications.append(classification.to_dict(for_different_project))

        return {"tools": all_tools, "classifications": all_classifications}

'''
EVERYTHING BELOW THIS LINE IS JUST FOR SELF TESTING
'''

def print_stuff():
    tools = o.tools
    classifications = o.classifications

    print("tools\n")
    for tool in tools:
        print("\n",tool)
    print("\nclassifications\n")
    for classification in classifications:
        print("\n",classification)

if __name__ == "__main__":
    os.system('clear')
    apikey = os.environ['apikey']
    client = Client(apikey) 
    project = client.get_project("ckhchkye62xn30796uui5lu34")

    # client = Client(apikey)
    # project = client.get_project("ckkyi8ih56sc207570tb35of1")
   
    o = Ontology().from_project(project)

    
    #create a Point tool and add a nested dropdown in it
    # tool = o.add_tool(tool = Tool.Type.POINT, name = "Example Point Tool")
    # nested_class = tool.add_nested_class(class_type = Classification.Type.DROPDOWN, instructions = "nested class")
    # dropdown_option = nested_class.add_option(value="answer")

    # tool = o.add_tool(tool = Tool.Type.NER, name="NER value")

    #to old existing project
    frontend = list(client.get_labeling_frontends(where=LabelingFrontend.name == "Editor"))[0]
    project.setup(frontend, o.build(for_different_project=False))

    #to a different project
    # other_project = client.get_project("ckkzzw5qk1yje0712uqjn0oqs")
    # other_project.setup(frontend, o.build(for_different_project=True))





