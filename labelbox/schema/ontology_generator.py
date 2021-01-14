from dataclasses import dataclass, field
from enum import Enum, auto
import os
from typing import List, Optional

from labelbox import Client, Project, Dataset, LabelingFrontend

class InconsistentOntologyException(Exception):
    pass

@dataclass
class Option():
    value: str    
    label: str = None
    schema_id: Optional[str] = None
    feature_schema_id: Optional[str] = None

    def __post_init__(self):
        self.label = self.value
    

@dataclass
class Classification():

    class Type(Enum):
        TEXT = "text"
        CHECKLIST = "checklist"
        RADIO = "radio"
        DROPDOWN = "dropdown"

    type: Type
    instructions: str
    name: str = None
    required: bool = False
    options: List[Option] = field(default_factory=list)
    schema_id: Optional[str] = None
    feature_schema_id: Optional[str] = None

    def __post_init__(self):
        self.name = self.instructions
  

@dataclass
class Tool():

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

    # @classmethod
    # def _from_existing_ontology(cls, dict):
    #     for key,value in dict.items():
    #         print(key,value)


@dataclass
class Ontology():
    
    tools: List[Tool] = field(default_factory=list)
    classifications: List[Classification] = field(default_factory=list)

    @classmethod
    def from_project(cls, project: Project):
        ontology = project.ontology().normalized
        return_ontology = Ontology()

        for tool in ontology['tools']:
            tool['schema_id'] = tool.pop('schemaNodeId')
            tool['feature_schema_id'] = tool.pop('featureSchemaId')
            tool['tool'] = Tool.Type(tool['tool'])
            return_ontology.add_tool(**tool)

        for classification in ontology['classifications']:
            classification['schema_id'] = classification.pop('schemaNodeId')
            classification['feature_schema_id'] = classification.pop('featureSchemaId')
            classification['type'] = Classification.Type(classification['type'])
            return_ontology.add_classification(**classification)
 
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
        self.all_tools = []
        self.all_classifications = []

        for tool in self.tools:
            curr_tool = dict((key,value) for (key,value) in tool.__dict__.items())
            curr_tool['tool'] = curr_tool['tool'].value
            curr_tool['schemaNodeId'] = curr_tool.pop('schema_id')
            curr_tool['featureSchemaId'] = curr_tool.pop('feature_schema_id')
            self.all_tools.append(curr_tool)

        for classification in self.classifications:
            curr_classification = dict((key,value) for (key,value) in classification.__dict__.items())
            curr_classification['type'] = curr_classification['type'].value
            curr_classification['schemaNodeId'] = curr_classification.pop('schema_id')
            curr_classification['featureSchemaId'] = curr_classification.pop('feature_schema_id')
            self.all_classifications.append(curr_classification)

        return {"tools": self.all_tools, "classifications": self.all_classifications}


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
    o.add_tool(tool=Tool.Type.SEGMENTATION, name="hello world")

    run()

    



'''
TODO
work on enforcing certain classifications need options (and work on other things other than text)

create an example of a classification with options

work on nesting classes inside tools

work on nesting classes inside other classes

in the future: work on adding NER capability for tool types (?)


TODO: Questions for Florjian:
1. when taking in an ontology from an existing project, I converted 'schemaNodeId' to schema_id and 'featureSchemaId' to feature_schema_id. 
   then, when planning to move setup the project with the new ontology, I converted them back to the original id's. Is it better to do it
   this way because it follows PEP8? or should I just change the naming conventino of the variables?

2. I am a little confused on what is the best way to enforce certain classifications require a series of options. My last version basically had a list
   of Classification.Type that if it fell into that list, it would require options before it could be created. What is the best way to do this?

3. My ontology class is getting a little long because I am manually changing certain dict keys to another key (part of #1's problem). Is there a 
   better way to do dict key renaming?

4. I was thinking instead of lines 79-81 and 85-87 could be converted to @classmethods instead of what I am doing now. Would that be better?
'''

