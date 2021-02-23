# import unittest
import pytest
from typing import Any, Dict, List, Union
from labelbox import LabelingFrontend

#want to import ontology_generator.py properly, not the bad way we are currently doing
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

#want to create base case tests, each indiv tool, classification, option
#want to then do nested objects inside each
#do we want to test colors, bool, etc?
#test inside methods? like asdict/fromdict?
#test ontology.from_project?
#test ontology.build?
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
    o = Ontology()
    assert(o.tools == [])
    assert(o.classifications == [])

def test_create_ontology(client, project) -> None:
    """ Tests that the ontology that a project was set up with can be grabbed."""
    frontend = list(
        client.get_labeling_frontends(
            where=LabelingFrontend.name == "Editor"))[0]
    project.setup(frontend, sample_ontology())
    normalized_ontology = project.ontology().normalized

    def _remove_schema_ids(
            ontology_part: Union[List, Dict[str, Any]]) -> Dict[str, Any]:
        """ Recursively scrub the normalized ontology of any schema information."""
        removals = {'featureSchemaId', 'schemaNodeId'}

        if isinstance(ontology_part, list):
            return [_remove_schema_ids(part) for part in ontology_part]
        if isinstance(ontology_part, dict):
            return {
                key: _remove_schema_ids(value)
                for key, value in ontology_part.items()
                if key not in removals
            }
        return ontology_part

    removed = _remove_schema_ids(normalized_ontology)
    assert removed == sample_ontology()

    ontology = project.ontology()

    tools = ontology.tools()
    assert tools
    for tool in tools:
        assert tool.feature_schema_id
        assert tool.schema_node_id

    classifications = ontology.classifications()
    assert classifications
    for classification in classifications:
        assert classification.feature_schema_id
        assert classification.schema_node_id
        for option in classification.options:
            assert option.feature_schema_id
            assert option.schema_node_id

