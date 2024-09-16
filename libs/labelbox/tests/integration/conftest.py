from collections import defaultdict
from itertools import islice
import json
import os
import sys
import re
import time
import uuid
import requests
from types import SimpleNamespace
from typing import Type, List
from enum import Enum
from typing import Tuple

import pytest
import requests

from labelbox import Dataset, DataRow
from labelbox import LabelingFrontend
from labelbox import (
    OntologyBuilder,
    Tool,
    Option,
    Classification,
    MediaType,
    PromptResponseClassification,
    ResponseOption,
)
from labelbox.orm import query
from labelbox.pagination import PaginatedCollection
from labelbox.schema.annotation_import import LabelImport
from labelbox.schema.catalog import Catalog
from labelbox.schema.enums import AnnotationImportState
from labelbox.schema.invite import Invite
from labelbox.schema.quality_mode import QualityMode
from labelbox.schema.queue_mode import QueueMode
from labelbox.schema.user import User
from labelbox import Client
from labelbox.schema.ontology_kind import OntologyKind


@pytest.fixture
def project_based_user(client, rand_gen):
    email = rand_gen(str)
    # Use old mutation because it doesn't require users to accept email invites
    query_str = """mutation MakeNewUserPyApi {
        addMembersToOrganization(
            data: {
                emails: ["%s@labelbox.com"],
                orgRoleId: "%s",
                projectRoles: []
            }
        ) {
        newUserId
        }
    }
    """ % (email, str(client.get_roles()["NONE"].uid))
    user_id = client.execute(query_str)["addMembersToOrganization"][0][
        "newUserId"
    ]
    assert user_id is not None, "Unable to add user with old mutation"
    user = client._get_single(User, user_id)
    yield user
    client.get_organization().remove_user(user)


@pytest.fixture
def project_pack(client):
    projects = [
        client.create_project(
            name=f"user-proj-{idx}",
            queue_mode=QueueMode.Batch,
            media_type=MediaType.Image,
        )
        for idx in range(2)
    ]
    yield projects
    for proj in projects:
        proj.delete()


@pytest.fixture
def project_with_empty_ontology(project):
    editor = list(
        project.client.get_labeling_frontends(
            where=LabelingFrontend.name == "editor"
        )
    )[0]
    empty_ontology = {"tools": [], "classifications": []}
    project.setup(editor, empty_ontology)
    yield project


@pytest.fixture
def configured_project(
    project_with_empty_ontology, initial_dataset, rand_gen, image_url
):
    dataset = initial_dataset
    data_row_id = dataset.create_data_row(row_data=image_url).uid
    project = project_with_empty_ontology

    batch = project.create_batch(
        rand_gen(str),
        [data_row_id],  # sample of data row objects
        5,  # priority between 1(Highest) - 5(lowest)
    )
    project.data_row_ids = [data_row_id]

    yield project

    batch.delete()


@pytest.fixture
def configured_project_with_complex_ontology(
    client, initial_dataset, rand_gen, image_url, teardown_helpers
):
    project = client.create_project(
        name=rand_gen(str),
        queue_mode=QueueMode.Batch,
        media_type=MediaType.Image,
    )
    dataset = initial_dataset
    data_row = dataset.create_data_row(row_data=image_url)
    data_row_ids = [data_row.uid]

    project.create_batch(
        rand_gen(str),
        data_row_ids,  # sample of data row objects
        5,  # priority between 1(Highest) - 5(lowest)
    )
    project.data_row_ids = data_row_ids

    editor = list(
        project.client.get_labeling_frontends(
            where=LabelingFrontend.name == "editor"
        )
    )[0]

    ontology = OntologyBuilder()
    tools = [
        Tool(tool=Tool.Type.BBOX, name="test-bbox-class"),
        Tool(tool=Tool.Type.LINE, name="test-line-class"),
        Tool(tool=Tool.Type.POINT, name="test-point-class"),
        Tool(tool=Tool.Type.POLYGON, name="test-polygon-class"),
        Tool(tool=Tool.Type.NER, name="test-ner-class"),
    ]

    options = [
        Option(value="first option answer"),
        Option(value="second option answer"),
        Option(value="third option answer"),
    ]

    classifications = [
        Classification(
            class_type=Classification.Type.TEXT, name="test-text-class"
        ),
        Classification(
            class_type=Classification.Type.RADIO,
            name="test-radio-class",
            options=options,
        ),
        Classification(
            class_type=Classification.Type.CHECKLIST,
            name="test-checklist-class",
            options=options,
        ),
    ]

    for t in tools:
        for c in classifications:
            t.add_classification(c)
        ontology.add_tool(t)
    for c in classifications:
        ontology.add_classification(c)

    project.setup(editor, ontology.asdict())

    yield [project, data_row]
    teardown_helpers.teardown_project_labels_ontology_feature_schemas(project)


@pytest.fixture
def ontology(client):
    ontology_builder = OntologyBuilder(
        tools=[
            Tool(tool=Tool.Type.BBOX, name="Box 1", color="#ff0000"),
            Tool(tool=Tool.Type.BBOX, name="Box 2", color="#ff0000"),
        ],
        classifications=[
            Classification(
                name="Root Class",
                class_type=Classification.Type.RADIO,
                options=[
                    Option(value="1", label="Option 1"),
                    Option(value="2", label="Option 2"),
                ],
            )
        ],
    )
    ontology = client.create_ontology(
        "Integration Test Ontology", ontology_builder.asdict(), MediaType.Image
    )
    yield ontology
    client.delete_unused_ontology(ontology.uid)


@pytest.fixture
def video_data(client, rand_gen, video_data_row, wait_for_data_row_processing):
    dataset = client.create_dataset(name=rand_gen(str))
    data_row_ids = []
    data_row = dataset.create_data_row(video_data_row)
    data_row = wait_for_data_row_processing(client, data_row)
    data_row_ids.append(data_row.uid)
    yield dataset, data_row_ids
    dataset.delete()


def create_video_data_row(rand_gen):
    return {
        "row_data": "https://storage.googleapis.com/labelbox-datasets/video-sample-data/sample-video-1.mp4",
        "global_key": f"https://storage.googleapis.com/labelbox-datasets/video-sample-data/sample-video-1.mp4-{rand_gen(str)}",
        "media_type": "VIDEO",
    }


@pytest.fixture
def video_data_100_rows(client, rand_gen, wait_for_data_row_processing):
    dataset = client.create_dataset(name=rand_gen(str))
    data_row_ids = []
    for _ in range(100):
        data_row = dataset.create_data_row(create_video_data_row(rand_gen))
        data_row = wait_for_data_row_processing(client, data_row)
        data_row_ids.append(data_row.uid)
    yield dataset, data_row_ids
    dataset.delete()


@pytest.fixture()
def video_data_row(rand_gen):
    return create_video_data_row(rand_gen)


class ExportV2Helpers:
    @classmethod
    def run_project_export_v2_task(
        cls, project, num_retries=5, task_name=None, filters={}, params={}
    ):
        task = None
        params = (
            params
            if params
            else {
                "project_details": True,
                "performance_details": False,
                "data_row_details": True,
                "label_details": True,
            }
        )
        while num_retries > 0:
            task = project.export_v2(
                task_name=task_name, filters=filters, params=params
            )
            task.wait_till_done()
            assert task.status == "COMPLETE"
            assert task.errors is None
            if len(task.result) == 0:
                num_retries -= 1
                time.sleep(5)
            else:
                break
        return task.result

    @classmethod
    def run_dataset_export_v2_task(
        cls, dataset, num_retries=5, task_name=None, filters={}, params={}
    ):
        task = None
        params = (
            params
            if params
            else {"performance_details": False, "label_details": True}
        )
        while num_retries > 0:
            task = dataset.export_v2(
                task_name=task_name, filters=filters, params=params
            )
            task.wait_till_done()
            assert task.status == "COMPLETE"
            assert task.errors is None
            if len(task.result) == 0:
                num_retries -= 1
                time.sleep(5)
            else:
                break

        return task.result

    @classmethod
    def run_catalog_export_v2_task(
        cls, client, num_retries=5, task_name=None, filters={}, params={}
    ):
        task = None
        params = (
            params
            if params
            else {"performance_details": False, "label_details": True}
        )
        catalog = client.get_catalog()
        while num_retries > 0:
            task = catalog.export_v2(
                task_name=task_name, filters=filters, params=params
            )
            task.wait_till_done()
            assert task.status == "COMPLETE"
            assert task.errors is None
            if len(task.result) == 0:
                num_retries -= 1
                time.sleep(5)
            else:
                break

        return task.result


@pytest.fixture
def export_v2_test_helpers() -> Type[ExportV2Helpers]:
    return ExportV2Helpers()


@pytest.fixture
def big_dataset_data_row_ids(big_dataset: Dataset):
    export_task = big_dataset.export()
    export_task.wait_till_done()
    stream = export_task.get_buffered_stream()
    yield [dr.json["data_row"]["id"] for dr in stream]


@pytest.fixture(scope="function")
def dataset_with_invalid_data_rows(
    unique_dataset: Dataset, upload_invalid_data_rows_for_dataset
):
    upload_invalid_data_rows_for_dataset(unique_dataset)

    yield unique_dataset


@pytest.fixture
def upload_invalid_data_rows_for_dataset():
    def _upload_invalid_data_rows_for_dataset(dataset: Dataset):
        task = dataset.create_data_rows(
            [
                {
                    "row_data": "gs://invalid-bucket/example.png",  # forbidden
                    "external_id": "image-without-access.jpg",
                },
            ]
            * 2
        )
        task.wait_till_done()

    return _upload_invalid_data_rows_for_dataset


@pytest.fixture
def prompt_response_generation_project_with_new_dataset(
    client: Client, rand_gen, request
):
    """fixture is parametrize and needs project_type in request"""
    media_type = request.param
    prompt_response_project = client.create_prompt_response_generation_project(
        name=f"{media_type.value}-{rand_gen(str)}",
        dataset_name=f"{media_type.value}-{rand_gen(str)}",
        data_row_count=1,
        media_type=media_type,
    )

    yield prompt_response_project

    prompt_response_project.delete()


@pytest.fixture
def prompt_response_generation_project_with_dataset_id(
    client: Client, dataset, rand_gen, request
):
    """fixture is parametrized and needs project_type in request"""
    media_type = request.param
    prompt_response_project = client.create_prompt_response_generation_project(
        name=f"{media_type.value}-{rand_gen(str)}",
        dataset_id=dataset.uid,
        data_row_count=1,
        media_type=media_type,
    )

    yield prompt_response_project

    prompt_response_project.delete()


@pytest.fixture
def response_creation_project(client: Client, rand_gen):
    project_name = f"response-creation-project-{rand_gen(str)}"
    project = client.create_response_creation_project(name=project_name)

    yield project

    project.delete()


@pytest.fixture
def prompt_response_features(rand_gen):
    prompt_text = PromptResponseClassification(
        class_type=PromptResponseClassification.Type.PROMPT,
        name=f"{rand_gen(str)}-prompt text",
    )

    response_radio = PromptResponseClassification(
        class_type=PromptResponseClassification.Type.RESPONSE_RADIO,
        name=f"{rand_gen(str)}-response radio classification",
        options=[
            ResponseOption(value=f"{rand_gen(str)}-first radio option answer"),
            ResponseOption(value=f"{rand_gen(str)}-second radio option answer"),
        ],
    )

    response_checklist = PromptResponseClassification(
        class_type=PromptResponseClassification.Type.RESPONSE_CHECKLIST,
        name=f"{rand_gen(str)}-response checklist classification",
        options=[
            ResponseOption(
                value=f"{rand_gen(str)}-first checklist option answer"
            ),
            ResponseOption(
                value=f"{rand_gen(str)}-second checklist option answer"
            ),
        ],
    )

    response_text_with_char = PromptResponseClassification(
        class_type=PromptResponseClassification.Type.RESPONSE_TEXT,
        name=f"{rand_gen(str)}-response text with character min and max",
        character_min=1,
        character_max=10,
    )

    response_text = PromptResponseClassification(
        class_type=PromptResponseClassification.Type.RESPONSE_TEXT,
        name=f"{rand_gen(str)}-response text",
    )

    nested_response_radio = PromptResponseClassification(
        class_type=PromptResponseClassification.Type.RESPONSE_RADIO,
        name=f"{rand_gen(str)}-nested response radio classification",
        options=[
            ResponseOption(
                f"{rand_gen(str)}-first_radio_answer",
                options=[
                    PromptResponseClassification(
                        class_type=PromptResponseClassification.Type.RESPONSE_RADIO,
                        name=f"{rand_gen(str)}-sub_radio_question",
                        options=[
                            ResponseOption(
                                f"{rand_gen(str)}-first_sub_radio_answer"
                            )
                        ],
                    )
                ],
            )
        ],
    )
    yield {
        "prompts": [prompt_text],
        "responses": [
            response_text,
            response_radio,
            response_checklist,
            response_text_with_char,
            nested_response_radio,
        ],
    }


@pytest.fixture
def prompt_response_ontology(
    client: Client, rand_gen, prompt_response_features, request
):
    """fixture is parametrize and needs project_type in request"""

    project_type = request.param
    if project_type == MediaType.LLMPromptCreation:
        ontology_builder = OntologyBuilder(
            tools=[], classifications=prompt_response_features["prompts"]
        )
    elif project_type == MediaType.LLMPromptResponseCreation:
        ontology_builder = OntologyBuilder(
            tools=[],
            classifications=prompt_response_features["prompts"]
            + prompt_response_features["responses"],
        )
    else:
        ontology_builder = OntologyBuilder(
            tools=[], classifications=prompt_response_features["responses"]
        )

    ontology_name = f"prompt-response-{rand_gen(str)}"

    if project_type in MediaType:
        ontology = client.create_ontology(
            ontology_name, ontology_builder.asdict(), media_type=project_type
        )
    else:
        ontology = client.create_ontology(
            ontology_name,
            ontology_builder.asdict(),
            media_type=MediaType.Text,
            ontology_kind=OntologyKind.ResponseCreation,
        )
    yield ontology

    featureSchemaIds = [
        feature["featureSchemaId"]
        for feature in ontology.normalized["classifications"]
    ]

    try:
        client.delete_unused_ontology(ontology.uid)
        for featureSchemaId in featureSchemaIds:
            client.delete_unused_feature_schema(featureSchemaId)
    except Exception as e:
        print(f"Failed to delete ontology {ontology.uid}: {str(e)}")


@pytest.fixture
def point():
    return Tool(
        tool=Tool.Type.POINT,
        name="name",
        color="#ff0000",
    )


@pytest.fixture
def feature_schema(client, point):
    created_feature_schema = client.upsert_feature_schema(point.asdict())

    yield created_feature_schema
    client.delete_unused_feature_schema(
        created_feature_schema.normalized["featureSchemaId"]
    )


@pytest.fixture
def chat_evaluation_ontology(client, rand_gen):
    ontology_name = f"test-chat-evaluation-ontology-{rand_gen(str)}"
    ontology_builder = OntologyBuilder(
        tools=[
            Tool(
                tool=Tool.Type.MESSAGE_SINGLE_SELECTION,
                name="model output single selection",
            ),
            Tool(
                tool=Tool.Type.MESSAGE_MULTI_SELECTION,
                name="model output multi selection",
            ),
            Tool(
                tool=Tool.Type.MESSAGE_RANKING,
                name="model output multi ranking",
            ),
        ],
        classifications=[
            Classification(
                class_type=Classification.Type.TEXT,
                name="global model output text classification",
                scope=Classification.Scope.GLOBAL,
            ),
            Classification(
                class_type=Classification.Type.RADIO,
                name="global model output radio classification",
                scope=Classification.Scope.GLOBAL,
                options=[
                    Option(value="global first option answer"),
                    Option(value="global second option answer"),
                ],
            ),
            Classification(
                class_type=Classification.Type.CHECKLIST,
                name="global model output checklist classification",
                scope=Classification.Scope.GLOBAL,
                options=[
                    Option(value="global first option answer"),
                    Option(value="global second option answer"),
                ],
            ),
            Classification(
                class_type=Classification.Type.TEXT,
                name="index model output text classification",
                scope=Classification.Scope.INDEX,
            ),
            Classification(
                class_type=Classification.Type.RADIO,
                name="index model output radio classification",
                scope=Classification.Scope.INDEX,
                options=[
                    Option(value="index first option answer"),
                    Option(value="index second option answer"),
                ],
            ),
            Classification(
                class_type=Classification.Type.CHECKLIST,
                name="index model output checklist classification",
                scope=Classification.Scope.INDEX,
                options=[
                    Option(value="index first option answer"),
                    Option(value="index second option answer"),
                ],
            ),
        ],
    )

    ontology = client.create_ontology(
        ontology_name,
        ontology_builder.asdict(),
        media_type=MediaType.Conversational,
        ontology_kind=OntologyKind.ModelEvaluation,
    )

    yield ontology

    try:
        client.delete_unused_ontology(ontology.uid)
    except Exception as e:
        print(f"Failed to delete ontology {ontology.uid}: {str(e)}")


@pytest.fixture
def live_chat_evaluation_project_with_new_dataset(client, rand_gen):
    project_name = f"test-model-evaluation-project-{rand_gen(str)}"
    dataset_name = f"test-model-evaluation-dataset-{rand_gen(str)}"
    project = client.create_model_evaluation_project(
        name=project_name, dataset_name=dataset_name, data_row_count=1
    )

    yield project

    project.delete()


@pytest.fixture
def offline_chat_evaluation_project(client, rand_gen):
    project_name = f"test-offline-model-evaluation-project-{rand_gen(str)}"
    project = client.create_offline_model_evaluation_project(name=project_name)

    yield project

    project.delete()


@pytest.fixture
def chat_evaluation_project_append_to_dataset(client, dataset, rand_gen):
    project_name = f"test-model-evaluation-project-{rand_gen(str)}"
    dataset_id = dataset.uid
    project = client.create_model_evaluation_project(
        name=project_name, dataset_id=dataset_id, data_row_count=1
    )

    yield project

    project.delete()


@pytest.fixture
def offline_conversational_data_row(initial_dataset):
    convo_v2_row_data = {
        "type": "application/vnd.labelbox.conversational.model-chat-evaluation",
        "version": 2,
        "actors": {
            "clxhs9wk000013b6w7imiz0h8": {
                "role": "human",
                "metadata": {"name": "User"},
            },
            "clxhsc6xb00013b6w1awh579j": {
                "role": "model",
                "metadata": {
                    "modelConfigId": "5a50d319-56bd-405d-87bb-4442daea0d0f"
                },
            },
            "clxhsc6xb00023b6wlp0768zs": {
                "role": "model",
                "metadata": {
                    "modelConfigId": "1cfc833a-2684-47df-95ac-bb7d9f9e3e1f"
                },
            },
        },
        "messages": {
            "clxhs9wk000023b6wrufora3k": {
                "actorId": "clxhs9wk000013b6w7imiz0h8",
                "content": [{"type": "text", "content": "Hello world"}],
                "childMessageIds": ["clxhscb4z00033b6wukpvmuol"],
            },
            "clxhscb4z00033b6wukpvmuol": {
                "actorId": "clxhsc6xb00013b6w1awh579j",
                "content": [
                    {
                        "type": "text",
                        "content": "Hello to you too! 👋 \n\nIt's great to be your guide in the digital world. What can I help you with today? 😊 \n",
                    }
                ],
                "childMessageIds": ["clxhu2s0900013b6wbv0ndddd"],
            },
            "clxhu2s0900013b6wbv0ndddd": {
                "actorId": "clxhs9wk000013b6w7imiz0h8",
                "content": [
                    {
                        "type": "text",
                        "content": "Lets some some multi-turn happening",
                    }
                ],
                "childMessageIds": [
                    "clxhu4qib00023b6wuep47b1l",
                    "clxhu4qib00033b6wf18az01q",
                ],
            },
            "clxhu4qib00023b6wuep47b1l": {
                "actorId": "clxhsc6xb00013b6w1awh579j",
                "content": [
                    {
                        "type": "text",
                        "content": "Okay, I'm ready for some multi-turn fun! To make it interesting, how about we try building a story together? \n\n**Here's the beginning:**\n\nThe old, dusty book lay forgotten on the shelf, its leather cover cracked and faded. But as the afternoon sun slanted through the window, a single ray caught a glint of gold on the book's spine. Suddenly...\n\n**Now you tell me what happens!** What does the glint of gold turn out to be? What happens next? 🤔 \n",
                    }
                ],
                "childMessageIds": ["clxhu596m00043b6wvkgahcwz"],
            },
            "clxhu4qib00033b6wf18az01q": {
                "actorId": "clxhsc6xb00023b6wlp0768zs",
                "content": [
                    {
                        "type": "text",
                        "content": "Okay, I'm game! Let's have a multi-turn conversation! But to get us started, give me a topic or a question to get us going! 😄 \n\nWhat's on your mind? \n",
                    }
                ],
                "childMessageIds": ["clxhu596m00043b6wvkgahcwz"],
            },
            "clxhu596m00043b6wvkgahcwz": {
                "actorId": "clxhs9wk000013b6w7imiz0h8",
                "content": [
                    {"type": "text", "content": "Can you generate an image?"}
                ],
                "childMessageIds": [
                    "clxhu5hqk00053b6wk21u6xi7",
                    "clxhu5hqk00063b6whl4gofx8",
                ],
            },
            "clxhu5hqk00053b6wk21u6xi7": {
                "actorId": "clxhsc6xb00013b6w1awh579j",
                "content": [
                    {
                        "type": "text",
                        "content": "I can't generate images directly yet. I'm a text-based AI, so my superpowers are all about words! 🪄 \n\nHowever, I'd love to help you describe an image that fits our story. Tell me: \n\n* **What should the image show?** (For example: The dusty book, the glint of gold, the bookshelf, the room, etc.) \n* **What kind of feeling or atmosphere should the image have?** (Mysterious? Magical? Ominous?) \n\nThe more details you give me, the better I can describe the image! ✨ \n",
                    }
                ],
                "childMessageIds": [],
            },
            "clxhu5hqk00063b6whl4gofx8": {
                "actorId": "clxhsc6xb00023b6wlp0768zs",
                "content": [
                    {
                        "type": "text",
                        "content": "I can't *actually* generate images directly. 😔 I'm primarily a text-based AI. \n\nTo help me understand what you'd like to see, tell me: \n\n* **What should be in the image?** Be specific! (e.g., \"A cat wearing a tiny hat\", \"A futuristic cityscape at sunset\")\n* **What style do you imagine?** (e.g., realistic, cartoonish, abstract)\n\nOnce you give me those details, I can try to give you a vivid description that's almost as good as seeing it! 😊 \n",
                    }
                ],
                "childMessageIds": [],
            },
        },
        "rootMessageIds": ["clxhs9wk000023b6wrufora3k"],
    }

    convo_v2_asset = {
        "row_data": convo_v2_row_data,
    }
    data_row = initial_dataset.create_data_row(convo_v2_asset)

    return data_row


@pytest.fixture
def response_data_row(initial_dataset):
    text_asset = {"row_data": "response sample text"}
    data_row = initial_dataset.create_data_row(text_asset)

    return data_row


@pytest.fixture()
def conversation_data_row(initial_dataset, rand_gen):
    data = {
        "row_data": "https://storage.googleapis.com/labelbox-developer-testing-assets/conversational_text/1000-conversations/conversation-1.json",
        "global_key": f"https://storage.googleapis.com/labelbox-developer-testing-assets/conversational_text/1000-conversations/conversation-1.json-{rand_gen(str)}",
    }
    convo_asset = {"row_data": data}
    data_row = initial_dataset.create_data_row(convo_asset)

    return data_row


def pytest_configure():
    pytest.report = defaultdict(int)


@pytest.hookimpl(hookwrapper=True)
def pytest_fixture_setup(fixturedef):
    start = time.time()
    yield
    end = time.time()

    exec_time = end - start
    if "FIXTURE_PROFILE" in os.environ:
        pytest.report[fixturedef.argname] += exec_time


@pytest.fixture(scope="session", autouse=True)
def print_perf_summary():
    yield

    if "FIXTURE_PROFILE" in os.environ:
        sorted_dict = dict(
            sorted(
                pytest.report.items(), key=lambda item: item[1], reverse=True
            )
        )
        num_of_entries = 10 if len(sorted_dict) >= 10 else len(sorted_dict)
        slowest_fixtures = [
            (aaa, sorted_dict[aaa])
            for aaa in islice(sorted_dict, num_of_entries)
        ]
        print("\nTop slowest fixtures:\n", slowest_fixtures, file=sys.stderr)
