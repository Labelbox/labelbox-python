import pytest
from unittest.mock import patch

from labelbox import MediaType
from labelbox.schema.ontology_kind import OntologyKind
from labelbox.exceptions import MalformedQueryException


@pytest.mark.parametrize(
    "prompt_response_ontology, prompt_response_generation_project_with_new_dataset",
    [
        (MediaType.LLMPromptCreation, MediaType.LLMPromptCreation),
        (
            MediaType.LLMPromptResponseCreation,
            MediaType.LLMPromptResponseCreation,
        ),
    ],
    indirect=True,
)
def test_prompt_response_generation_ontology_project(
    client,
    prompt_response_ontology,
    prompt_response_generation_project_with_new_dataset,
    response_data_row,
    rand_gen,
):
    ontology = prompt_response_ontology

    assert ontology
    assert ontology.name

    for classification in ontology.classifications():
        assert classification.schema_id
        assert classification.feature_schema_id

    project = prompt_response_generation_project_with_new_dataset

    project.connect_ontology(ontology)

    assert project.labeling_frontend().name == "Editor"
    assert project.ontology().name == ontology.name

    with pytest.raises(
        ValueError,
        match="Cannot create batches for auto data generation projects",
    ):
        project.create_batch(
            rand_gen(str),
            [response_data_row.uid],  # sample of data row objects
        )

    with pytest.raises(
        ValueError,
        match="Cannot create batches for auto data generation projects",
    ):
        with patch(
            "labelbox.schema.project.MAX_SYNC_BATCH_ROW_COUNT", new=0
        ):  # force to async
            project.create_batch(
                rand_gen(str),
                [response_data_row.uid],  # sample of data row objects
            )


@pytest.mark.parametrize(
    "prompt_response_ontology, prompt_response_generation_project_with_dataset_id",
    [
        (MediaType.LLMPromptCreation, MediaType.LLMPromptCreation),
        (
            MediaType.LLMPromptResponseCreation,
            MediaType.LLMPromptResponseCreation,
        ),
    ],
    indirect=True,
)
def test_prompt_response_generation_ontology_project_with_existing_dataset(
    prompt_response_ontology, prompt_response_generation_project_with_dataset_id
):
    ontology = prompt_response_ontology

    project = prompt_response_generation_project_with_dataset_id
    assert project
    project.connect_ontology(ontology)

    assert project.labeling_frontend().name == "Editor"
    assert project.ontology().name == ontology.name


@pytest.fixture
def classification_json():
    classifications = [
        {
            "featureSchemaId": None,
            "kind": "Prompt",
            "minCharacters": 2,
            "maxCharacters": 10,
            "name": "prompt text",
            "instructions": "prompt text",
            "required": True,
            "schemaNodeId": None,
            "scope": "global",
            "type": "prompt",
            "options": [],
        },
        {
            "featureSchemaId": None,
            "kind": "ResponseCheckboxQuestion",
            "name": "response checklist",
            "instructions": "response checklist",
            "options": [
                {
                    "featureSchemaId": None,
                    "kind": "ResponseCheckboxOption",
                    "label": "response checklist option",
                    "schemaNodeId": None,
                    "position": 0,
                    "value": "option_1",
                }
            ],
            "required": True,
            "schemaNodeId": None,
            "scope": "global",
            "type": "response-checklist",
        },
        {
            "featureSchemaId": None,
            "kind": "ResponseText",
            "maxCharacters": 10,
            "minCharacters": 1,
            "name": "response text",
            "instructions": "response text",
            "required": True,
            "schemaNodeId": None,
            "scope": "global",
            "type": "response-text",
            "options": [],
        },
    ]

    return classifications


@pytest.fixture
def features_from_json(client, classification_json):
    classifications = classification_json
    features = {client.create_feature_schema(t) for t in classifications if t}

    yield features

    for f in features:
        client.delete_unused_feature_schema(f.uid)


@pytest.fixture
def ontology_from_feature_ids(client, features_from_json):
    feature_ids = {f.uid for f in features_from_json}
    ontology = client.create_ontology_from_feature_schemas(
        name="test-prompt_response_creation{rand_gen(str)}",
        feature_schema_ids=feature_ids,
        media_type=MediaType.LLMPromptResponseCreation,
    )

    yield ontology

    client.delete_unused_ontology(ontology.uid)


def test_ontology_create_feature_schema(
    ontology_from_feature_ids, features_from_json, classification_json
):
    created_ontology = ontology_from_feature_ids
    feature_schema_ids = {f.uid for f in features_from_json}
    classifications_normalized = created_ontology.normalized["classifications"]
    classifications = classification_json

    for classification in classifications:
        generated_tool = next(
            c
            for c in classifications_normalized
            if c["name"] == classification["name"]
        )
        assert generated_tool["schemaNodeId"] is not None
        assert generated_tool["featureSchemaId"] in feature_schema_ids
        assert generated_tool["type"] == classification["type"]
        assert generated_tool["name"] == classification["name"]
        assert generated_tool["required"] == classification["required"]
