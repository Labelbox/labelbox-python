import pytest
from typing import Any, Dict, List, Union
from labelbox import LabelingFrontend

from labelbox.schema.ontology_generator import Ontology, Tool, Classification, Option, InconsistentOntologyException

def sample_ontology() -> Dict[str, Any]:
    return {
        "tools": [{
            "required": False,
            "name": "Dog",
            "color": "#FF0000",
            "tool": "rectangle",
            "classifications": []
        }],
        "classifications": [{
            "required":
                True,
            "instructions":
                "This is a question.",
            "name":
                "this_is_a_question.",
            "type":
                "radio",
            "options": [{
                "label": "Yes",
                "value": "yes"
            }, {
                "label": "No",
                "value": "no"
            }]
        }]
    }

#test asdict
#test nested classifications
"""
Tool tests
"""
# def test_create_tool(client, project) -> None:
def test_create_bbox_tool() -> None:
    t = Tool(tool=Tool.Type.BBOX, name="box tool")
    assert(t.tool==Tool.Type.BBOX)
    assert(t.name=="box tool")

def test_create_point_tool() -> None:
    t = Tool(tool=Tool.Type.POINT, name="point tool")
    assert(t.tool==Tool.Type.POINT)
    assert(t.name=="point tool")    

def test_create_polygon_tool() -> None:
    t = Tool(tool=Tool.Type.POLYGON, name="polygon tool")
    assert(t.tool==Tool.Type.POLYGON)
    assert(t.name=="polygon tool")  

def test_create_ner_tool() -> None:
    t = Tool(tool=Tool.Type.NER, name="ner tool")
    assert(t.tool==Tool.Type.NER)
    assert(t.name=="ner tool")  

def test_create_segment_tool() -> None:
    t = Tool(tool=Tool.Type.SEGMENTATION, name="segment tool")
    assert(t.tool==Tool.Type.SEGMENTATION)
    assert(t.name=="segment tool")      

def test_create_line_tool() -> None:
    t = Tool(tool=Tool.Type.LINE, name="line tool")
    assert(t.tool==Tool.Type.LINE)
    assert(t.name=="line tool")  

"""
Classification tests
"""
def test_create_text_classification() -> None:
    c = Classification(class_type=Classification.Type.TEXT, instructions="text")
    assert(c.class_type==Classification.Type.TEXT)
    assert(c.instructions=="text")
    assert(c.class_type not in c._REQUIRES_OPTIONS)

def test_create_radio_classification() -> None:
    c = Classification(class_type=Classification.Type.RADIO, instructions="radio")
    assert(c.class_type==Classification.Type.RADIO)
    assert(c.instructions=="radio")
    assert(c.class_type in c._REQUIRES_OPTIONS)

def test_create_checklist_classification() -> None:
    c = Classification(class_type=Classification.Type.CHECKLIST, instructions="checklist")
    assert(c.class_type==Classification.Type.CHECKLIST)
    assert(c.instructions=="checklist")
    assert(c.class_type in c._REQUIRES_OPTIONS)

def test_create_dropdown_classification() -> None:
    c = Classification(class_type=Classification.Type.DROPDOWN, instructions="dropdown")
    assert(c.class_type==Classification.Type.DROPDOWN)
    assert(c.instructions=="dropdown")
    assert(c.class_type in c._REQUIRES_OPTIONS)

"""
Option tests
"""
def test_create_int_option() -> None:
    o = Option(value=3)
    assert(o.value==3)
    assert(type(o.value) == int)

def test_create_string_option() -> None:
    o = Option(value="3")
    assert(o.value=="3")
    assert(type(o.value)== str)

"""
Ontology tests
"""
def test_create_ontology() -> None:
    """
    Tests the initial structure of an Ontology object
    """
    o = Ontology()
    assert type(o) == Ontology
    assert(o.tools == [])
    assert(o.classifications == [])

def test_add_ontology_tool() -> None:
    """
    Tests the possible ways to add a tool to an ontology
    """
    o = Ontology()
    o.add_tool(Tool(tool = Tool.Type.BBOX, name = "bounding box"))

    second_tool = Tool(tool = Tool.Type.SEGMENTATION, name = "segmentation")
    o.add_tool(second_tool)

    for tool in o.tools:
        assert type(tool) == Tool

def test_add_ontology_classification() -> None:
    """
    Tests the possible ways to add a classification to an ontology
    """
    o = Ontology()
    o.add_classification(Classification(
        class_type = Classification.Type.TEXT, instructions = "text"))

    second_classification = Classification(
        class_type = Classification.Type.CHECKLIST, instructions = "checklist")
    o.add_classification(second_classification)

    for classification in o.classifications:
        assert type(classification) == Classification

def test_ontology_asdict(project) -> None:
    """
    Tests the asdict() method to ensure that it matches the format 
    of a project ontology
    """
    from_project_ontology = project.ontology().normalized

    o = Ontology.from_project(project)
    assert o.asdict() == from_project_ontology

def test_from_project_ontology(client, project) -> None:
    """
    Tests the ability to correctly get an existing project's ontology
        and if it can correctly convert it to the right object types
    """
    frontend = list(
        client.get_labeling_frontends(
            where=LabelingFrontend.name == "Editor"))[0]
    project.setup(frontend, sample_ontology())
    
    ontology = Ontology.from_project(project)
    assert len(ontology.tools) == 1
    assert ontology.tools[0].tool == Tool.Type.BBOX
    for tool in ontology.tools:
        assert type(tool) == Tool

    assert len(ontology.classifications) == 1
    assert ontology.classifications[0].class_type == Classification.Type.RADIO
    for classification in ontology.classifications:
        assert type(classification) == Classification

    assert len(ontology.classifications[0].options) == 2
    assert ontology.classifications[0].options[0].value.lower() == "yes"
    assert ontology.classifications[0].options[0].label.lower() == "yes"
    for option in ontology.classifications[0].options:
        assert type(option) == Option




    

"""
Old ontology file test
"""
# def test_create_ontology(client, project) -> None:
#     """ Tests that the ontology that a project was set up with can be grabbed."""
#     frontend = list(
#         client.get_labeling_frontends(
#             where=LabelingFrontend.name == "Editor"))[0]
#     project.setup(frontend, sample_ontology())
#     normalized_ontology = project.ontology().normalized

#     def _remove_schema_ids(
#             ontology_part: Union[List, Dict[str, Any]]) -> Dict[str, Any]:
#         """ Recursively scrub the normalized ontology of any schema information."""
#         removals = {'featureSchemaId', 'schemaNodeId'}

#         if isinstance(ontology_part, list):
#             return [_remove_schema_ids(part) for part in ontology_part]
#         if isinstance(ontology_part, dict):
#             return {
#                 key: _remove_schema_ids(value)
#                 for key, value in ontology_part.items()
#                 if key not in removals
#             }
#         return ontology_part

#     removed = _remove_schema_ids(normalized_ontology)
#     assert removed == sample_ontology()

#     ontology = project.ontology()

#     tools = ontology.tools()
#     assert tools
#     for tool in tools:
#         assert tool.feature_schema_id
#         assert tool.schema_node_id

#     classifications = ontology.classifications()
#     assert classifications
#     for classification in classifications:
#         assert classification.feature_schema_id
#         assert classification.schema_node_id
#         for option in classification.options:
#             assert option.feature_schema_id
#             assert option.schema_node_id

