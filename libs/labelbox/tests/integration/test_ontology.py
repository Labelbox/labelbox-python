import json
import time

import pytest

from labelbox import MediaType, OntologyBuilder, OntologyKind, Tool
from labelbox.orm.model import Entity
from labelbox.schema.tool_building.classification import Classification, Option
from labelbox.schema.tool_building.fact_checking_tool import (
    FactCheckingTool,
)
from labelbox.schema.tool_building.prompt_issue_tool import PromptIssueTool
from labelbox.schema.tool_building.step_reasoning_tool import (
    StepReasoningTool,
)
from labelbox.schema.tool_building.tool_type import ToolType


def test_feature_schema_is_not_archived(client, ontology):
    feature_schema_to_check = ontology.normalized["tools"][0]
    result = client.is_feature_schema_archived(
        ontology.uid, feature_schema_to_check["featureSchemaId"]
    )
    assert result is False


def test_feature_schema_is_archived(client, configured_project_with_label):
    project, _, _, label = configured_project_with_label
    ontology = project.ontology()
    feature_schema_id = ontology.normalized["tools"][0]["featureSchemaId"]
    result = client.delete_feature_schema_from_ontology(
        ontology.uid, feature_schema_id
    )
    assert result.archived is True and result.deleted is False
    assert (
        client.is_feature_schema_archived(ontology.uid, feature_schema_id)
        is True
    )


def test_is_feature_schema_archived_for_non_existing_feature_schema(
    client, ontology
):
    with pytest.raises(
        Exception, match="The specified feature schema was not in the ontology"
    ):
        client.is_feature_schema_archived(
            ontology.uid, "invalid-feature-schema-id"
        )


def test_is_feature_schema_archived_for_non_existing_ontology(client, ontology):
    feature_schema_to_unarchive = ontology.normalized["tools"][0]
    with pytest.raises(
        Exception,
        match="Resource 'Ontology' not found for params: 'invalid-ontology'",
    ):
        client.is_feature_schema_archived(
            "invalid-ontology", feature_schema_to_unarchive["featureSchemaId"]
        )


def test_delete_tool_feature_from_ontology(client, ontology):
    feature_schema_to_delete = ontology.normalized["tools"][0]
    assert len(ontology.normalized["tools"]) == 2
    result = client.delete_feature_schema_from_ontology(
        ontology.uid, feature_schema_to_delete["featureSchemaId"]
    )
    assert result.deleted is True
    assert result.archived is False
    updatedOntology = client.get_ontology(ontology.uid)
    assert len(updatedOntology.normalized["tools"]) == 1


@pytest.mark.skip(
    reason="normalized ontology contains Relationship, "
    "which is not finalized yet. introduce this back when"
    "Relationship feature is complete and we introduce"
    "a Relationship object to the ontology that we can parse"
)
def test_from_project_ontology(project) -> None:
    o = OntologyBuilder.from_project(project)
    assert o.asdict() == project.ontology().normalized


point = Tool(
    tool=Tool.Type.POINT,
    name="name",
    color="#ff0000",
)


def test_deletes_an_ontology(client):
    tool = client.upsert_feature_schema(point.asdict())
    feature_schema_id = tool.normalized["featureSchemaId"]
    ontology = client.create_ontology_from_feature_schemas(
        name="ontology name",
        feature_schema_ids=[feature_schema_id],
        media_type=MediaType.Image,
    )

    assert client.delete_unused_ontology(ontology.uid) is None

    client.delete_unused_feature_schema(feature_schema_id)


def test_cant_delete_an_ontology_with_project(client):
    project = client.create_project(
        name="test project",
        media_type=MediaType.Image,
    )
    tool = client.upsert_feature_schema(point.asdict())
    feature_schema_id = tool.normalized["featureSchemaId"]
    ontology = client.create_ontology_from_feature_schemas(
        name="ontology name",
        feature_schema_ids=[feature_schema_id],
        media_type=MediaType.Image,
    )
    project.connect_ontology(ontology)

    with pytest.raises(
        Exception,
        match="Failed to delete the ontology, message: Cannot delete an ontology connected to a project. The ontology is connected to projects: "
        + project.uid,
    ):
        client.delete_unused_ontology(ontology.uid)

    project.delete()
    client.delete_unused_ontology(ontology.uid)
    client.delete_unused_feature_schema(feature_schema_id)


def test_inserts_a_feature_schema_at_given_position(client):
    tool1 = {"tool": "polygon", "name": "tool1", "color": "blue"}
    tool2 = {"tool": "polygon", "name": "tool2", "color": "blue"}
    ontology_normalized_json = {"tools": [tool1, tool2], "classifications": []}
    ontology = client.create_ontology(
        name="ontology",
        normalized=ontology_normalized_json,
        media_type=MediaType.Image,
    )
    created_feature_schema = client.upsert_feature_schema(point.asdict())
    client.insert_feature_schema_into_ontology(
        created_feature_schema.normalized["featureSchemaId"], ontology.uid, 1
    )
    ontology = client.get_ontology(ontology.uid)

    assert (
        ontology.normalized["tools"][1]["schemaNodeId"]
        == created_feature_schema.normalized["schemaNodeId"]
    )

    client.delete_unused_ontology(ontology.uid)


def test_moves_already_added_feature_schema_in_ontology(client):
    tool1 = {"tool": "polygon", "name": "tool1", "color": "blue"}
    ontology_normalized_json = {"tools": [tool1], "classifications": []}
    ontology = client.create_ontology(
        name="ontology",
        normalized=ontology_normalized_json,
        media_type=MediaType.Image,
    )
    created_feature_schema = client.upsert_feature_schema(point.asdict())
    feature_schema_id = created_feature_schema.normalized["featureSchemaId"]
    client.insert_feature_schema_into_ontology(
        feature_schema_id, ontology.uid, 1
    )
    ontology = client.get_ontology(ontology.uid)
    assert (
        ontology.normalized["tools"][1]["schemaNodeId"]
        == created_feature_schema.normalized["schemaNodeId"]
    )
    client.insert_feature_schema_into_ontology(
        feature_schema_id, ontology.uid, 0
    )
    ontology = client.get_ontology(ontology.uid)

    assert (
        ontology.normalized["tools"][0]["schemaNodeId"]
        == created_feature_schema.normalized["schemaNodeId"]
    )

    client.delete_unused_ontology(ontology.uid)


def test_does_not_include_used_ontologies(client):
    tool = client.upsert_feature_schema(point.asdict())
    feature_schema_id = tool.normalized["featureSchemaId"]
    ontology_with_project = client.create_ontology_from_feature_schemas(
        name="ontology name",
        feature_schema_ids=[feature_schema_id],
        media_type=MediaType.Image,
    )
    project = client.create_project(
        name="test project",
        media_type=MediaType.Image,
    )
    project.connect_ontology(ontology_with_project)
    unused_ontologies = client.get_unused_ontologies()

    assert ontology_with_project.uid not in unused_ontologies

    project.delete()
    client.delete_unused_ontology(ontology_with_project.uid)
    client.delete_unused_feature_schema(feature_schema_id)


def _get_attr_stringify_json(obj, attr):
    value = getattr(obj, attr.name)
    if attr.field_type.name.lower() == "json":
        return json.dumps(value, sort_keys=True)
    return value


@pytest.fixture
def name_for_read(rand_gen):
    yield f"test-root-schema-{rand_gen(str)}"


@pytest.fixture
def feature_schema_cat_normalized(name_for_read):
    yield {
        "tool": "polygon",
        "name": name_for_read,
        "color": "black",
        "classifications": [],
    }


@pytest.fixture
def feature_schema_for_read(client, feature_schema_cat_normalized):
    feature_schema = client.create_feature_schema(feature_schema_cat_normalized)
    yield feature_schema
    client.delete_unused_feature_schema(feature_schema.uid)


def test_feature_schema_create_read(
    client, feature_schema_for_read, name_for_read
):
    created_feature_schema = feature_schema_for_read
    queried_feature_schema = client.get_feature_schema(
        created_feature_schema.uid
    )
    for attr in Entity.FeatureSchema.fields():
        assert _get_attr_stringify_json(
            created_feature_schema, attr
        ) == _get_attr_stringify_json(queried_feature_schema, attr)

    time.sleep(3)  # Slight delay for searching
    queried_feature_schemas = list(client.get_feature_schemas(name_for_read))
    assert [
        feature_schema.name for feature_schema in queried_feature_schemas
    ] == [name_for_read]
    queried_feature_schema = queried_feature_schemas[0]

    for attr in Entity.FeatureSchema.fields():
        assert _get_attr_stringify_json(
            created_feature_schema, attr
        ) == _get_attr_stringify_json(queried_feature_schema, attr)


def test_ontology_create_read(
    client,
    rand_gen,
):
    ontology_name = f"test-ontology-{rand_gen(str)}"
    tool_name = f"test-ontology-tool-{rand_gen(str)}"
    feature_schema_cat_normalized = {
        "tool": "polygon",
        "name": tool_name,
        "color": "black",
        "classifications": [],
    }
    feature_schema = client.create_feature_schema(feature_schema_cat_normalized)
    created_ontology = client.create_ontology_from_feature_schemas(
        name=ontology_name,
        feature_schema_ids=[feature_schema.uid],
        media_type=MediaType.Image,
    )
    tool_normalized = created_ontology.normalized["tools"][0]
    for k, v in feature_schema_cat_normalized.items():
        assert tool_normalized[k] == v
    assert tool_normalized["schemaNodeId"] is not None
    assert tool_normalized["featureSchemaId"] == feature_schema.uid

    queried_ontology = client.get_ontology(created_ontology.uid)

    for attr in Entity.Ontology.fields():
        assert _get_attr_stringify_json(
            created_ontology, attr
        ) == _get_attr_stringify_json(queried_ontology, attr)

    time.sleep(3)  # Slight delay for searching
    queried_ontologies = list(client.get_ontologies(ontology_name))
    assert [ontology.name for ontology in queried_ontologies] == [ontology_name]
    queried_ontology = queried_ontologies[0]
    for attr in Entity.Ontology.fields():
        assert _get_attr_stringify_json(
            created_ontology, attr
        ) == _get_attr_stringify_json(queried_ontology, attr)


def test_unarchive_feature_schema_node(client, ontology):
    feature_schema_to_unarchive = ontology.normalized["tools"][0]
    result = client.unarchive_feature_schema_node(
        ontology.uid, feature_schema_to_unarchive["featureSchemaId"]
    )
    assert result is None


def test_unarchive_feature_schema_node_for_non_existing_feature_schema(
    client, ontology
):
    with pytest.raises(
        Exception,
        match="Failed to find feature schema node by id: invalid-feature-schema-id",
    ):
        client.unarchive_feature_schema_node(
            ontology.uid, "invalid-feature-schema-id"
        )


def test_unarchive_feature_schema_node_for_non_existing_ontology(
    client, ontology
):
    feature_schema_to_unarchive = ontology.normalized["tools"][0]
    with pytest.raises(
        Exception, match="Failed to find ontology by id: invalid-ontology"
    ):
        client.unarchive_feature_schema_node(
            "invalid-ontology", feature_schema_to_unarchive["featureSchemaId"]
        )


def test_step_reasoning_ontology(chat_evaluation_ontology):
    ontology = chat_evaluation_ontology
    step_reasoning_tool = None
    for tool in ontology.normalized["tools"]:
        if tool["tool"] == "step-reasoning":
            step_reasoning_tool = tool
            break
    assert step_reasoning_tool is not None
    assert step_reasoning_tool["definition"]["variants"] == [
        {"id": 0, "name": "Correct", "actions": []},
        {"id": 1, "name": "Neutral", "actions": []},
        {
            "id": 2,
            "name": "Incorrect",
            "actions": [
                "regenerateSteps",
                "generateAndRateAlternativeSteps",
                "rewriteStep",
                "justification",
            ],
        },
    ]
    assert step_reasoning_tool["definition"]["version"] == 1
    assert step_reasoning_tool["schemaNodeId"] is not None
    assert step_reasoning_tool["featureSchemaId"] is not None

    step_reasoning_tool = None
    for tool in ontology.tools():
        if isinstance(tool, StepReasoningTool):
            step_reasoning_tool = tool
            break
    assert step_reasoning_tool is not None

    assert step_reasoning_tool.definition.asdict() == {
        "title": "step reasoning",
        "value": "step_reasoning",
        "variants": [
            {
                "id": 0,
                "name": "Correct",
                "actions": [],
            },
            {
                "id": 1,
                "name": "Neutral",
                "actions": [],
            },
            {
                "id": 2,
                "name": "Incorrect",
                "actions": [
                    "regenerateSteps",
                    "generateAndRateAlternativeSteps",
                    "rewriteStep",
                    "justification",
                ],
            },
        ],
        "version": 1,
    }


def test_fact_checking_ontology(chat_evaluation_ontology):
    ontology = chat_evaluation_ontology
    fact_checking = None
    for tool in ontology.normalized["tools"]:
        if tool["tool"] == "fact-checking":
            fact_checking = tool
            break
    assert fact_checking is not None
    assert fact_checking["definition"]["variants"] == [
        {"id": 0, "name": "Accurate", "actions": ["justification"]},
        {"id": 1, "name": "Inaccurate", "actions": ["justification"]},
        {"id": 2, "name": "Disputed", "actions": ["justification"]},
        {"id": 3, "name": "Unsupported", "actions": []},
        {
            "id": 4,
            "name": "Can't confidently assess",
            "actions": [],
        },
        {
            "id": 5,
            "name": "No factual information",
            "actions": [],
        },
    ]
    assert fact_checking["definition"]["version"] == 1
    assert fact_checking["schemaNodeId"] is not None
    assert fact_checking["featureSchemaId"] is not None

    fact_checking = None
    for tool in ontology.tools():
        if isinstance(tool, FactCheckingTool):
            fact_checking = tool
            break
    assert fact_checking is not None

    assert fact_checking.definition.asdict() == {
        "title": "fact checking",
        "value": "fact_checking",
        "variants": [
            {"id": 0, "name": "Accurate", "actions": ["justification"]},
            {"id": 1, "name": "Inaccurate", "actions": ["justification"]},
            {"id": 2, "name": "Disputed", "actions": ["justification"]},
            {"id": 3, "name": "Unsupported", "actions": []},
            {
                "id": 4,
                "name": "Can't confidently assess",
                "actions": [],
            },
            {
                "id": 5,
                "name": "No factual information",
                "actions": [],
            },
        ],
        "version": 1,
    }


def test_prompt_issue_ontology(chat_evaluation_ontology):
    ontology = chat_evaluation_ontology
    prompt_issue = None
    for tool in ontology.normalized["tools"]:
        if tool["tool"] == "prompt-issue":
            prompt_issue = tool
            break
    assert prompt_issue is not None

    assert prompt_issue["definition"] == {
        "title": "prompt issue",
        "value": "prompt_issue",
        "color": "#ff00ff",
    }
    assert prompt_issue["schemaNodeId"] is not None
    assert prompt_issue["featureSchemaId"] is not None
    assert len(prompt_issue["classifications"]) == 1

    prompt_issue_tool = None
    for tool in ontology.tools():
        if isinstance(tool, PromptIssueTool):
            prompt_issue_tool = tool
            break
    assert prompt_issue_tool is not None
    # Assertions
    assert prompt_issue_tool.name == "prompt issue"
    assert prompt_issue_tool.type == ToolType.PROMPT_ISSUE
    assert prompt_issue_tool.schema_id is not None
    assert prompt_issue_tool.feature_schema_id is not None

    # Check classifications
    assert len(prompt_issue_tool.classifications) == 1
    classification = prompt_issue_tool.classifications[0]
    assert classification.class_type == Classification.Type.CHECKLIST
    assert len(classification.options) == 3  # Check number of options


def test_invalid_prompt_issue_ontology(client):
    tool = PromptIssueTool(name="Prompt Issue Tool")

    option1 = Option(value="value")
    radio_class = Classification(
        class_type=Classification.Type.RADIO,
        name="radio-class",
        options=[option1],
    )
    text_class = Classification(
        class_type=Classification.Type.TEXT, name="text-class"
    )

    tool.classifications.append(radio_class)
    tool.classifications.append(text_class)

    builder = OntologyBuilder(
        tools=[tool],
    )
    with pytest.raises(
        ValueError, match="Classifications for Prompt Issue Tool are invalid"
    ):
        client.create_ontology(
            name="plt-1710",
            media_type=MediaType.Conversational,
            ontology_kind=OntologyKind.ModelEvaluation,
            normalized=builder.asdict(),
        )
