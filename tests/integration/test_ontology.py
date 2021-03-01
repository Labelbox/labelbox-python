"""
TODO:
test option.add_option
test all classes' asdicts (what is the best way...)
test classification.add_option
test tool.add_classification
consider testing and ensuring failed scenarios
"""
from typing import Any, Dict, List, Union

import pytest

from labelbox import LabelingFrontend
from labelbox.schema.ontology_generator import Ontology, \
    Tool, Classification, Option, InconsistentOntologyException


_SAMPLE_ONTOLOGY = {
        "tools": [{
            "required": False,
            "name": "Dog",
            "color": "#FF0000",
            "tool": "rectangle",
            "classifications": []
}],
        "classifications": [{
            "required": True,
            "instructions": "This is a question.",
            "name": "This is a question.",
            "type": "radio",
            "options": [{
                "label": "yes",
                "value": "yes"
            }, {
                "label": "no",
                "value": "no"
            }]
        }]
    }

@pytest.mark.parametrize("tool_type", list(Tool.Type))
@pytest.mark.parametrize("tool_name", ["tool"])
def test_create_tool(tool_type, tool_name) -> None:
    t = Tool(tool = tool_type, name = tool_name)
    assert(t.tool == tool_type)
    assert(t.name == tool_name)

@pytest.mark.parametrize("class_type", list(Classification.Type))
@pytest.mark.parametrize("class_instr", ["classification"])
def test_create_classification(class_type, class_instr) -> None:
    c = Classification(class_type = class_type, instructions = class_instr)
    assert(c.class_type == class_type)
    assert(c.instructions == class_instr)
    assert(c.name == c.instructions)

@pytest.mark.parametrize(
    "value, expected_value, typing",[(3,3, int),("string","string", str)])
def test_create_option(value, expected_value, typing) -> None:
    o = Option(value = value)
    assert(o.value == expected_value)
    assert(o.value == o.label)
    assert(type(o.value) == typing)

def test_create_empty_ontology() -> None:
    o = Ontology()
    assert(o.tools == [])
    assert(o.classifications == [])

def test_add_ontology_tool() -> None:
    o = Ontology()
    o.add_tool(Tool(tool = Tool.Type.BBOX, name = "bounding box"))

    second_tool = Tool(tool = Tool.Type.SEGMENTATION, name = "segmentation")
    o.add_tool(second_tool)

    assert len(o.tools) == 2

def test_add_ontology_classification() -> None:
    o = Ontology()
    o.add_classification(Classification(
        class_type = Classification.Type.TEXT, instructions = "text"))

    second_classification = Classification(
        class_type = Classification.Type.CHECKLIST, instructions = "checklist")
    o.add_classification(second_classification)

    assert len(o.classifications) == 2

def test_ontology_asdict(project) -> None:
    o = Ontology.from_project(project)
    assert o.asdict() == project.ontology().normalized

def test_from_project_ontology(client, project) -> None:
    frontend = list(
        client.get_labeling_frontends(
            where=LabelingFrontend.name == "Editor"))[0]
    project.setup(frontend, _SAMPLE_ONTOLOGY)    
    o = Ontology.from_project(project)

    assert o.tools[0].tool == Tool.Type.BBOX
    assert o.classifications[0].class_type == Classification.Type.RADIO
    assert o.classifications[0].options[0].value.lower() == "yes"

    
    
