'''
TODO
currently allows creation of a TEXT classification and options inside this file
↑ should not be possible, and in fact causes some unintended behavior when creating the ontology (creates options as a totally new classification)
↑ need to ensure that with TEXT we cannot embed options

validate prior to submission, so likely in the o.build() - like have a way to make sure that classifications that need options have options

work on enforcing certain classifications need options (and work on other things other than text)

create an example of a classification with options

work on nesting classes inside tools (and properly extrapolating the options when taking it from inside a project)

work on nesting classes inside other classes

maybe there should be a way to check if a project has an existing ontology, and that it would overwrite it?

in the future: work on adding NER capability for tool types (?)
'''

from dataclasses import dataclass, field
from enum import Enum, auto
import os
from typing import List, Optional

from labelbox import Client, Project, Dataset, LabelingFrontend


class InconsistentOntologyException(Exception):
    pass

@dataclass
class Option:
    value: str    
    schema_id: Optional[str] = None
    feature_schema_id: Optional[str] = None

    @property
    def label(self):
        return self.value

    @classmethod
    def option_class_to_dict(cls, option):
        return {
            "schemaNodeId": option.schema_id,
            "featureSchemaId": option.feature_schema_id,
            "label": option.value,
            "value": option.value
        }
    

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

    tool: Type 
    name: str 
    required: bool = False
    color: str = "#000000"
    classifications: List[Classification] = field(default_factory=list)
    schema_id: Optional[str] = None
    feature_schema_id: Optional[str] = None

@dataclass
class Ontology:
    
    tools: List[Tool] = field(default_factory=list)
    classifications: List[Classification] = field(default_factory=list)

    @classmethod
    def from_project(cls, project: Project):
        ontology = project.ontology().normalized
        return_ontology = Ontology()

        for tool in ontology["tools"]:      
            return_ontology.add_tool(
                name=tool['name'],
                schema_id=tool["schemaNodeId"],
                feature_schema_id=tool["featureSchemaId"],
                required=tool["required"],
                tool=Tool.Type(tool["tool"]),                
                classifications=tool["classifications"],
                color=tool["color"],
            )

        for classification in ontology["classifications"]:
            return_ontology.add_classification(
                schema_id=classification["schemaNodeId"], 
                feature_schema_id=classification["schemaNodeId"],
                required=classification["required"],
                instructions=classification["instructions"],
                class_type=Classification.Type(classification["type"]),
                options = [Option(value=option["value"], schema_id=option["schemaNodeId"], feature_schema_id=option["featureSchemaId"]) for option in classification["options"] if len(classification["options"]) > 0]
            )
 
        return return_ontology

    def add_tool(self, *args, **kwargs):
        new_tool = Tool(*args, **kwargs)
        if new_tool.name in (tool.name for tool in self.tools):
            raise InconsistentOntologyException(f"Duplicate tool name '{new_tool.name}'. ")
        self.tools.append(new_tool)
        return new_tool

    def add_classification(self, *args, **kwargs):
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
                "classifications": tool.classifications,
                "schemaNodeId": tool.schema_id,
                "featureSchemaId": tool.feature_schema_id

            })

        for classification in self.classifications:
            all_classifications.append({
                "type": classification.class_type.value,
                "instructions": classification.instructions,
                "name": classification.name,
                "required": classification.required,
                # "options": classification.options,
                "options": [Option.option_class_to_dict(option) for option in classification.options],
                "schemaNodeId": classification.schema_id,
                "featureSchemaId": classification.feature_schema_id
            })

        return {"tools": all_tools, "classifications": all_classifications}


#made this just to test in my own project. not keeping this
def run():
    frontend = list(client.get_labeling_frontends(where=LabelingFrontend.name == "Editor"))[0]
    project.setup(frontend, o.build())
    return project

if __name__ == "__main__":
    import json
    os.system('clear')
    apikey = os.environ['apikey']
    client = Client(apikey) 
    project = client.get_project("ckhchkye62xn30796uui5lu34")

    o = Ontology().from_project(project)
    
    o.add_tool(tool=Tool.Type.POLYGON, name="i am a polygon tool")
    checklist = o.add_classification(class_type=Classification.Type.CHECKLIST, instructions="I AM A CHECKLIST")
    checklist.add_option(value="checklist answer 1")
    checklist.add_option(value="checklist answer 2")


    print(o.build())
    run()