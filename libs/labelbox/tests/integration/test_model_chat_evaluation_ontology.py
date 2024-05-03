from labelbox import OntologyBuilder, Tool


def test_create_model_chat_evaluation_ontology(client, rand_gen):
    ontology_name = f"test-model-chat-evaluation-ontology-{rand_gen(str)}"
    ontology_builder = OntologyBuilder(
        tools=[
            Tool(tool=Tool.Type.MODEL_OUTPUT_SINGLE_SELECTION, name="model output single selection"),
            Tool(tool=Tool.Type.MODEL_OUTPUT_MULTI_SELECTION, name="model output multi selection"),
            Tool(tool=Tool.Type.MODEL_OUTPUT_MULTI_RANKING, name="model output multi ranking"),
        ],
    )
    ontology = None

    try:
        ontology = client.create_model_chat_evaluation_ontology(ontology_name, ontology_builder.asdict())
        assert ontology
        assert ontology.name == ontology_name
        assert len(ontology.tools()) == 3
        for tool in ontology.tools():
            assert tool.schema_id
            assert tool.feature_schema_id

    finally:
        if ontology:
            client.delete_unused_ontology(ontology.uid)
