import pytest
from labelbox import OntologyBuilder, Tool
from labelbox import MediaType


def test_create_model_chat_evaluation_ontology(model_chat_evaluation_ontology):
    ontology = model_chat_evaluation_ontology

    # here we are essentially testing the ontology creation which is a fixture
    assert ontology
    assert ontology.name
    assert len(ontology.tools()) == 3
    for tool in ontology.tools():
        assert tool.schema_id
        assert tool.feature_schema_id


@pytest.fixture
def tools_json():
    tools = [{
        'tool': 'message-single-selection',
        'name': 'model output single selection',
        'required': False,
        'color': '#ff0000',
        'classifications': [],
        'schemaNodeId': None,
        'featureSchemaId': None
    }, {
        'tool': 'message-multi-selection',
        'name': 'model output multi selection',
        'required': False,
        'color': '#00ff00',
        'classifications': [],
        'schemaNodeId': None,
        'featureSchemaId': None
    }, {
        'tool': 'message-ranking',
        'name': 'model output multi ranking',
        'required': False,
        'color': '#0000ff',
        'classifications': [],
        'schemaNodeId': None,
        'featureSchemaId': None
    }]

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
    ontology = client.create_model_chat_evaluation_ontology_from_feature_schemas(
        name="test-model-chat-evaluation-ontology{rand_gen(str)}",
        feature_schema_ids=feature_ids,
    )

    yield ontology

    client.delete_unused_ontology(ontology.uid)


def test_ontology_create_feature_schema(ontology_from_feature_ids, features_from_json, tools_json):
    created_ontology = ontology_from_feature_ids
    feature_schema_ids = {f.uid for f in features_from_json}
    tools_normalized = created_ontology.normalized['tools']
    tools = tools_json

    for tool in tools:
        generated_tool = next(
            t for t in tools_normalized if t['name'] == tool['name'])
        assert generated_tool['schemaNodeId'] is not None
        assert generated_tool['featureSchemaId'] in feature_schema_ids
        assert generated_tool['tool'] == tool['tool']
        assert generated_tool['name'] == tool['name']
        assert generated_tool['required'] == tool['required']
        assert generated_tool['color'] == tool['color']
