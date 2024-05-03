from labelbox import OntologyBuilder, Tool
from labelbox import MediaType


def test_create_model_chat_evaluation_ontology(client, rand_gen):
    ontology_name = f"test-model-chat-evaluation-ontology-{rand_gen(str)}"
    ontology_builder = OntologyBuilder(tools=[
        Tool(tool=Tool.Type.MODEL_OUTPUT_SINGLE_SELECTION,
             name="model output single selection"),
        Tool(tool=Tool.Type.MODEL_OUTPUT_MULTI_SELECTION,
             name="model output multi selection"),
        Tool(tool=Tool.Type.MODEL_OUTPUT_MULTI_RANKING,
             name="model output multi ranking"),
    ],)
    ontology = None

    try:
        ontology = client.create_model_chat_evaluation_ontology(
            ontology_name, ontology_builder.asdict())
        assert ontology
        assert ontology.name == ontology_name
        assert len(ontology.tools()) == 3
        for tool in ontology.tools():
            assert tool.schema_id
            assert tool.feature_schema_id

    finally:
        if ontology:
            client.delete_unused_ontology(ontology.uid)


def test_ontology_create_feature_schema(client, rand_gen):
    try:
        created_ontology = None
        features = None
        ontology_name = f"test-model-chat-evaluation-ontology-from-features{rand_gen(str)}"
        tools = [{
            'tool': 'model-output-single-selection',
            'name': 'model output single selection',
            'required': False,
            'color': '#ff0000',
            'classifications': [],
            'schemaNodeId': None,
            'featureSchemaId': None
        }, {
            'tool': 'model-output-multi-selection',
            'name': 'model output multi selection',
            'required': False,
            'color': '#00ff00',
            'classifications': [],
            'schemaNodeId': None,
            'featureSchemaId': None
        }, {
            'tool': 'model-output-ranking',
            'name': 'model output multi ranking',
            'required': False,
            'color': '#0000ff',
            'classifications': [],
            'schemaNodeId': None,
            'featureSchemaId': None
        }]

        features = {client.create_feature_schema(t) for t in tools}
        feature_schema_ids = {f.uid for f in features}
        assert len(feature_schema_ids) == 3

        created_ontology = client.create_model_chat_evaluation_ontology_from_feature_schemas(
            name=ontology_name,
            feature_schema_ids=feature_schema_ids,
        )
        tools_normalized = created_ontology.normalized['tools']

        for tool in tools:
            generated_tool = next(
                t for t in tools_normalized if t['name'] == tool['name'])
            assert generated_tool['schemaNodeId'] is not None
            assert generated_tool['featureSchemaId'] in feature_schema_ids
            assert generated_tool['tool'] == tool['tool']
            assert generated_tool['name'] == tool['name']
            assert generated_tool['required'] == tool['required']
            assert generated_tool['color'] == tool['color']
    finally:
        if created_ontology:
            client.delete_unused_ontology(created_ontology.uid)
        if features:
            for f in features:
                client.delete_unused_feature_schema(f.uid)
