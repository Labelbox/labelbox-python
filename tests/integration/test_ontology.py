import unittest
from typing import Any, Dict, List, Union


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


def test_create_ontology(client, project) -> None:
    """ Tests that the ontology that a project was set up with can be grabbed."""
    frontend = list(client.get_labeling_frontends())[0]
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
