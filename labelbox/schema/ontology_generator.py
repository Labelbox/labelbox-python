'''
TODO
2. validate that we can pull in all sorts of project ontology classes
3. validate we can submit basic ones back in (fix build() method)
4. do the rest of the stuff below

currently allows creation of a TEXT classification and options inside this file
↑ should not be possible, and in fact causes some unintended behavior when creating the ontology (creates options as a totally new classification)
↑ need to ensure that with TEXT we cannot embed options

validate prior to submission, so likely in the o.build() - like have a way to make sure that classifications that need options have options

work on enforcing certain classifications need options (and work on other things other than text)

maybe there should be a way to check if a project has an existing ontology, and that it would overwrite it?

in the future: work on adding NER capability for tool types (?)

EXTRA
    #TODO: look into static methods and differences vs. class methods
'''

from dataclasses import dataclass, field
from enum import Enum, auto
import os
from typing import List, Optional

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
    #TODO: need to look further into how to make this so that the user cannot input anything here
    options: Optional[Classification] = None

    @property
    def label(self):
        return self.value
    
    def to_dict(self) -> dict:
        return {
            "schemaNodeId": self.schema_id,
            "featureSchemaId": self.feature_schema_id,
            "label": self.label,
            "value": self.value,
            "options": [classification.to_dict() for classification in self.options]
        }

    @classmethod
    def from_dict(cls, dictionary: dict):
        def has_nested_classifications(dictionary: dict):
            if "options" in dictionary.keys():
                return [Classification.from_dict(nested_class) for nested_class in dictionary["options"]]
            return list()

        return Option(
            value = dictionary["value"],
            schema_id = dictionary["schemaNodeId"],
            feature_schema_id = dictionary["featureSchemaId"],
            options = has_nested_classifications(dictionary)
        )
    

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

    @property
    def name(self):
        return self.instructions

    def to_dict(self) -> dict:
        return {
            "type": self.class_type.value,
            "instructions": self.instructions,
            "name": self.name,
            "required": self.required,
            "options": [option.to_dict() for option in self.options],
            "schemaNodeId": self.schema_id,
            "featureSchemaId": self.feature_schema_id
        }   

    @classmethod
    def from_dict(cls, dictionary: dict): 
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

@dataclass
class Tool:

    class Type(Enum):
        POLYGON = "polygon"
        SEGMENTATION = "superpixel"
        POINT = "point"
        BBOX = "rectangle"
        LINE = "line"

    tool: Type 
    name: str 
    required: bool = False
    color: str = "#000000"
    classifications: List[Classification] = field(default_factory=list)
    schema_id: Optional[str] = None
    feature_schema_id: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "tool": self.tool.value,
            "name": self.name,
            "required": self.required,
            "color": self.color,
            "classifications": self.classifications,
            "schemaNodeId": self.schema_id,
            "featureSchemaId": self.feature_schema_id
        }

    @classmethod 
    def from_dict(cls, dictionary: dict):
        return Tool(
            name = dictionary['name'],
            schema_id = dictionary["schemaNodeId"],
            feature_schema_id = dictionary["featureSchemaId"],
            required = dictionary["required"],
            tool = Tool.Type(dictionary["tool"]),   
            classifications = [Classification.from_dict(classification) for classification in dictionary["classifications"]],
            color = dictionary["color"]
        )



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

    def build(self):
        all_tools = []
        all_classifications = []

        for tool in self.tools:
            
            all_tools.append({
                "tool": tool.tool.value,
                "name": tool.name,
                "required": tool.required,
                "color": tool.color,
                "classifications": [classification.to_dict() for classification in tool.classifications],
                "schemaNodeId": tool.schema_id,
                "featureSchemaId": tool.feature_schema_id

            })

        for classification in self.classifications:
            all_classifications.append({
                "type": classification.class_type.value,
                "instructions": classification.instructions,
                "name": classification.name,
                "required": classification.required,
                "options": [option.to_dict() for option in classification.options],
                "schemaNodeId": classification.schema_id,
                "featureSchemaId": classification.feature_schema_id
            })

        return {"tools": all_tools, "classifications": all_classifications}

'''
EVERYTHING BELOW THIS LINE IS JUST FOR SELF TESTING
'''
def run():
    frontend = list(client.get_labeling_frontends(where=LabelingFrontend.name == "Editor"))[0]
    project.setup(frontend, o.build())
    return project

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
    import json
    os.system('clear')
    apikey = os.environ['apikey']
    client = Client(apikey) 
    project = client.get_project("ckhchkye62xn30796uui5lu34")

    o = Ontology().from_project(project)
    # print_stuff()
    
    
    o.add_tool(tool=Tool.Type.POLYGON, name="I AM HERE FOR TESTING")
    # checklist = o.add_classification(class_type=Classification.Type.CHECKLIST, instructions="I AM A CHECKLIST2")
    # checklist.add_option(value="checklist answer 1")
    # checklist.add_option(value="checklist answer 2")


    # print_stuff()
    # print(o.build())
    # print(type(o.build()))
    # print(o.build())
    run()

    





