from itertools import product

import pytest
from lbox.exceptions import InconsistentOntologyException

from labelbox import Classification, OntologyBuilder, Option, Tool

_SAMPLE_ONTOLOGY = {
    "tools": [
        {
            "schemaNodeId": None,
            "featureSchemaId": None,
            "required": False,
            "name": "poly",
            "color": "#FF0000",
            "tool": "polygon",
            "classifications": [],
            "attributes": None,
        },
        {
            "schemaNodeId": None,
            "featureSchemaId": None,
            "required": False,
            "name": "segment",
            "color": "#FF0000",
            "tool": "superpixel",
            "classifications": [],
            "attributes": None,
        },
        {
            "schemaNodeId": None,
            "featureSchemaId": None,
            "required": False,
            "name": "bbox",
            "color": "#FF0000",
            "tool": "rectangle",
            "attributes": [
                {
                    "attributeName": "auto-ocr",
                    "attributeValue": "true",
                }
            ],
            "classifications": [
                {
                    "schemaNodeId": None,
                    "featureSchemaId": None,
                    "required": True,
                    "instructions": "nested classification",
                    "name": "nested classification",
                    "type": "radio",
                    "uiMode": "searchable",
                    "options": [
                        {
                            "schemaNodeId": None,
                            "featureSchemaId": None,
                            "label": "first",
                            "value": "first",
                            "options": [
                                {
                                    "schemaNodeId": None,
                                    "featureSchemaId": None,
                                    "required": False,
                                    "instructions": "nested nested text",
                                    "name": "nested nested text",
                                    "type": "text",
                                    "options": [],
                                    "attributes": None,
                                }
                            ],
                        },
                        {
                            "schemaNodeId": None,
                            "featureSchemaId": None,
                            "label": "second",
                            "value": "second",
                            "options": [],
                        },
                    ],
                    "attributes": [
                        {
                            "attributeName": "requires-connection",
                            "attributeValue": "true",
                        }
                    ],
                },
                {
                    "schemaNodeId": None,
                    "featureSchemaId": None,
                    "required": True,
                    "instructions": "nested text",
                    "name": "nested text",
                    "type": "text",
                    "options": [],
                    "attributes": None,
                },
            ],
        },
        {
            "schemaNodeId": None,
            "featureSchemaId": None,
            "required": False,
            "name": "dot",
            "color": "#FF0000",
            "tool": "point",
            "classifications": [],
            "attributes": None,
        },
        {
            "schemaNodeId": None,
            "featureSchemaId": None,
            "required": False,
            "name": "polyline",
            "color": "#FF0000",
            "tool": "line",
            "classifications": [],
            "attributes": None,
        },
        {
            "schemaNodeId": None,
            "featureSchemaId": None,
            "required": False,
            "name": "ner",
            "color": "#FF0000",
            "tool": "named-entity",
            "classifications": [],
            "attributes": None,
        },
    ],
    "classifications": [
        {
            "schemaNodeId": None,
            "featureSchemaId": None,
            "required": True,
            "instructions": "This is a question.",
            "name": "This is a question.",
            "type": "radio",
            "scope": "global",
            "uiMode": "searchable",
            "attributes": None,
            "options": [
                {
                    "schemaNodeId": None,
                    "featureSchemaId": None,
                    "label": "yes",
                    "value": "definitely yes",
                    "options": [],
                },
                {
                    "schemaNodeId": None,
                    "featureSchemaId": None,
                    "label": "no",
                    "value": "definitely not",
                    "options": [],
                },
            ],
        }
    ],
}


@pytest.mark.parametrize("tool_type", list(Tool.Type))
def test_create_tool(tool_type) -> None:
    t = Tool(tool=tool_type, name="tool")
    assert t.tool == tool_type


@pytest.mark.parametrize("class_type", list(Classification.Type))
def test_create_classification(class_type) -> None:
    c = Classification(class_type=class_type, name="classification")
    assert c.class_type == class_type


@pytest.mark.parametrize(
    "ui_mode_type, class_type",
    list(product(list(Classification.UIMode), list(Classification.Type))),
)
def test_create_classification_with_ui_mode(ui_mode_type, class_type) -> None:
    c = Classification(
        name="classification", class_type=class_type, ui_mode=ui_mode_type
    )
    assert c.ui_mode == ui_mode_type


@pytest.mark.parametrize(
    "value, expected_value, typing", [(3, 3, int), ("string", "string", str)]
)
def test_create_option_with_value(value, expected_value, typing) -> None:
    o = Option(value=value)
    assert o.value == expected_value
    assert o.value == o.label


@pytest.mark.parametrize(
    "value, label, expected_value, typing",
    [(3, 2, 3, int), ("string", "another string", "string", str)],
)
def test_create_option_with_value_and_label(
    value, label, expected_value, typing
) -> None:
    o = Option(value=value, label=label)
    assert o.value == expected_value
    assert o.value != o.label
    assert isinstance(o.value, typing)


def test_create_empty_ontology() -> None:
    o = OntologyBuilder()
    assert o.tools == []
    assert o.classifications == []


def test_add_ontology_tool() -> None:
    o = OntologyBuilder()
    o.add_tool(Tool(tool=Tool.Type.BBOX, name="bounding box"))

    second_tool = Tool(tool=Tool.Type.SEGMENTATION, name="segmentation")
    o.add_tool(second_tool)
    assert len(o.tools) == 2

    for tool in o.tools:
        assert type(tool) is Tool

    with pytest.raises(InconsistentOntologyException) as exc:
        o.add_tool(Tool(tool=Tool.Type.BBOX, name="bounding box"))
    assert "Duplicate tool name" in str(exc.value)


def test_add_ontology_classification() -> None:
    o = OntologyBuilder()
    o.add_classification(
        Classification(class_type=Classification.Type.TEXT, name="text")
    )

    second_classification = Classification(
        class_type=Classification.Type.CHECKLIST, name="checklist"
    )
    o.add_classification(second_classification)
    assert len(o.classifications) == 2

    for classification in o.classifications:
        assert type(classification) is Classification

    with pytest.raises(InconsistentOntologyException) as exc:
        o.add_classification(
            Classification(class_type=Classification.Type.TEXT, name="text")
        )
    assert "Duplicate classification name" in str(exc.value)


def test_tool_add_classification() -> None:
    t = Tool(tool=Tool.Type.SEGMENTATION, name="segmentation")
    c = Classification(class_type=Classification.Type.TEXT, name="text")
    t.add_classification(c)
    assert t.classifications == [c]

    with pytest.raises(Exception) as exc:
        t.add_classification(c)
    assert "Duplicate nested classification" in str(exc)


def test_classification_add_option() -> None:
    c = Classification(class_type=Classification.Type.RADIO, name="radio")
    o = Option(value="option")
    c.add_option(o)
    assert c.options == [o]

    with pytest.raises(InconsistentOntologyException) as exc:
        c.add_option(Option(value="option"))
    assert "Duplicate option" in str(exc.value)


def test_option_add_option() -> None:
    o = Option(value="option")
    c = Classification(class_type=Classification.Type.TEXT, name="text")
    o.add_option(c)
    assert o.options == [c]

    with pytest.raises(InconsistentOntologyException) as exc:
        o.add_option(c)
    assert "Duplicate nested classification" in str(exc.value)


def test_ontology_asdict() -> None:
    assert (
        OntologyBuilder.from_dict(_SAMPLE_ONTOLOGY).asdict() == _SAMPLE_ONTOLOGY
    )


def test_classification_using_instructions_instead_of_name_shows_warning():
    with pytest.warns(Warning):
        Classification(class_type=Classification.Type.TEXT, instructions="text")


def test_classification_without_name_raises_error():
    with pytest.raises(ValueError):
        Classification(class_type=Classification.Type.TEXT)


@pytest.mark.parametrize(
    "class_type, is_likert_scale, should_include",
    [
        (Classification.Type.RADIO, True, True),
        (Classification.Type.RADIO, False, False),
        (Classification.Type.CHECKLIST, True, False),
        (Classification.Type.TEXT, True, False),
    ],
)
def test_is_likert_scale_serialization(
    class_type, is_likert_scale, should_include
):
    c = Classification(
        class_type=class_type, name="test", is_likert_scale=is_likert_scale
    )
    if class_type in Classification._REQUIRES_OPTIONS:
        c.add_option(Option(value="option1"))
    result = c.asdict()
    assert ("isLikertScale" in result) == should_include


def test_option_position_auto_assignment():
    c = Classification(class_type=Classification.Type.RADIO, name="test")
    o1, o2 = Option(value="first"), Option(value="second")
    c.add_option(o1)
    c.add_option(o2)
    assert o1.position == 0 and o2.position == 1
    assert c.asdict()["options"][0]["position"] == 0
