import pytest

from labelbox import MediaType
from labelbox.schema.ontology_kind import OntologyKind


def test_create_chat_evaluation_ontology_project(
    chat_evaluation_ontology,
    live_chat_evaluation_project,
    offline_conversational_data_row,
    rand_gen,
):
    ontology = chat_evaluation_ontology

    # here we are essentially testing the ontology creation which is a fixture
    assert ontology
    assert ontology.name
    assert len(ontology.tools()) == 6
    for tool in ontology.tools():
        assert tool.schema_id
        assert tool.feature_schema_id

    assert len(ontology.classifications()) == 6
    for classification in ontology.classifications():
        assert classification.schema_id
        assert classification.feature_schema_id

    project = live_chat_evaluation_project
    assert project.model_setup_complete is None

    project.connect_ontology(ontology)

    assert project.labeling_frontend().name == "Editor"
    assert project.ontology().name == ontology.name

    batch = project.create_batch(
        rand_gen(str),
        [offline_conversational_data_row.uid],  # sample of data row objects
    )
    assert batch


def test_create_chat_evaluation_ontology_project_existing_dataset(
    chat_evaluation_ontology, chat_evaluation_project_append_to_dataset
):
    ontology = chat_evaluation_ontology

    project = chat_evaluation_project_append_to_dataset
    assert project
    project.connect_ontology(ontology)

    assert project.labeling_frontend().name == "Editor"
    assert project.ontology().name == ontology.name


@pytest.fixture
def tools_json():
    tools = [
        {
            "tool": "message-single-selection",
            "name": "model output single selection",
            "required": False,
            "color": "#ff0000",
            "classifications": [],
            "schemaNodeId": None,
            "featureSchemaId": None,
        },
        {
            "tool": "message-multi-selection",
            "name": "model output multi selection",
            "required": False,
            "color": "#00ff00",
            "classifications": [],
            "schemaNodeId": None,
            "featureSchemaId": None,
        },
        {
            "tool": "message-ranking",
            "name": "model output multi ranking",
            "required": False,
            "color": "#0000ff",
            "classifications": [],
            "schemaNodeId": None,
            "featureSchemaId": None,
        },
        {
            "tool": "step-reasoning",
            "name": "step reasoning",
            "required": True,
            "schemaNodeId": None,
            "featureSchemaId": None,
            "color": "#0000ff",
            "definition": {
                "variants": [
                    {"id": 0, "name": "Correct", "actions": []},
                    {"id": 1, "name": "Neutral", "actions": []},
                    {
                        "id": 2,
                        "name": "Incorrect",
                        "actions": [
                            "regenerateSteps",
                            "generateAndRateAlternativeSteps",
                        ],
                    },
                ],
                "version": 1,
            },
        },
    ]

    return tools


@pytest.fixture
def features_from_json(client, tools_json):
    tools = tools_json
    features = {client.create_feature_schema(t) for t in tools if t}

    yield features

    for f in features:
        client.delete_unused_feature_schema(f.uid)


@pytest.fixture
def ontology_from_feature_ids(client, features_from_json):
    feature_ids = {f.uid for f in features_from_json}
    ontology = client.create_ontology_from_feature_schemas(
        name="test-model-chat-evaluation-ontology{rand_gen(str)}",
        feature_schema_ids=feature_ids,
        media_type=MediaType.Conversational,
        ontology_kind=OntologyKind.ModelEvaluation,
    )

    yield ontology

    client.delete_unused_ontology(ontology.uid)


def test_ontology_create_feature_schema(
    ontology_from_feature_ids, features_from_json, tools_json
):
    created_ontology = ontology_from_feature_ids
    feature_schema_ids = {f.uid for f in features_from_json}
    tools_normalized = created_ontology.normalized["tools"]
    tools = tools_json

    for tool in tools:
        generated_tool = next(
            t for t in tools_normalized if t["name"] == tool["name"]
        )
        assert generated_tool["schemaNodeId"] is not None
        assert generated_tool["featureSchemaId"] in feature_schema_ids
        assert generated_tool["tool"] == tool["tool"]
        assert generated_tool["name"] == tool["name"]
        assert generated_tool["required"] == tool["required"]
        assert generated_tool["color"] == tool["color"]
