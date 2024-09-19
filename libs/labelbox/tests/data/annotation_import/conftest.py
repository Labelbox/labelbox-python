import uuid
from typing import Union

from labelbox.schema.model_run import ModelRun
from labelbox.schema.ontology import Ontology
from labelbox.schema.project import Project
import pytest
import time
import requests

from labelbox import parser, MediaType, OntologyKind
from labelbox import Client, Dataset

from typing import Tuple, Type
from labelbox.schema.annotation_import import LabelImport, AnnotationImportState
from pytest import FixtureRequest

"""
The main fixtures of this library are configured_project and configured_project_by_global_key. Both fixtures generate data rows with a parametrize media type. They create the amount of data rows equal to the DATA_ROW_COUNT variable below. The data rows are generated with a factory fixture that returns a function that allows you to pass a global key. The ontologies are generated normalized and based on the MediaType given (i.e. only features supported by MediaType are created). This ontology is later used to obtain the correct annotations with the prediction_id_mapping and corresponding inferences. Each data row will have all possible annotations attached supported for the MediaType. 
"""

DATA_ROW_COUNT = 3
DATA_ROW_PROCESSING_WAIT_TIMEOUT_SECONDS = 40
DATA_ROW_PROCESSING_WAIT_SLEEP_INTERNAL_SECONDS = 7


@pytest.fixture(scope="module", autouse=True)
def video_data_row_factory():
    def video_data_row(global_key):
        return {
            "row_data": "https://storage.googleapis.com/labelbox-datasets/video-sample-data/sample-video-1.mp4",
            "global_key": f"https://storage.googleapis.com/labelbox-datasets/video-sample-data/sample-video-1.mp4-{global_key}",
            "media_type": "VIDEO",
        }

    return video_data_row


@pytest.fixture(scope="module", autouse=True)
def audio_data_row_factory():
    def audio_data_row(global_key):
        return {
            "row_data": "https://storage.googleapis.com/labelbox-datasets/audio-sample-data/sample-audio-1.mp3",
            "global_key": f"https://storage.googleapis.com/labelbox-datasets/audio-sample-data/sample-audio-1.mp3-{global_key}",
            "media_type": "AUDIO",
        }

    return audio_data_row


@pytest.fixture(scope="module", autouse=True)
def conversational_data_row_factory():
    def conversational_data_row(global_key):
        return {
            "row_data": "https://storage.googleapis.com/labelbox-developer-testing-assets/conversational_text/1000-conversations/conversation-1.json",
            "global_key": f"https://storage.googleapis.com/labelbox-developer-testing-assets/conversational_text/1000-conversations/conversation-1.json-{global_key}",
        }

    return conversational_data_row


@pytest.fixture(scope="module", autouse=True)
def dicom_data_row_factory():
    def dicom_data_row(global_key):
        return {
            "row_data": "https://storage.googleapis.com/labelbox-datasets/dicom-sample-data/sample-dicom-1.dcm",
            "global_key": f"https://storage.googleapis.com/labelbox-datasets/dicom-sample-data/sample-dicom-1.dcm-{global_key}",
            "media_type": "DICOM",
        }

    return dicom_data_row


@pytest.fixture(scope="module", autouse=True)
def geospatial_data_row_factory():
    def geospatial_data_row(global_key):
        return {
            "row_data": {
                "tile_layer_url": "https://s3-us-west-1.amazonaws.com/lb-tiler-layers/mexico_city/{z}/{x}/{y}.png",
                "bounds": [
                    [19.405662413477728, -99.21052827588443],
                    [19.400498983095076, -99.20534818927473],
                ],
                "min_zoom": 12,
                "max_zoom": 20,
                "epsg": "EPSG4326",
            },
            "global_key": f"https://s3-us-west-1.amazonaws.com/lb-tiler-layers/mexico_city/z/x/y.png-{global_key}",
            "media_type": "TMS_GEO",
        }

    return geospatial_data_row


@pytest.fixture(scope="module", autouse=True)
def html_data_row_factory():
    def html_data_row(global_key):
        return {
            "row_data": "https://storage.googleapis.com/labelbox-datasets/html_sample_data/sample_html_1.html",
            "global_key": f"https://storage.googleapis.com/labelbox-datasets/html_sample_data/sample_html_1.html-{global_key}",
        }

    return html_data_row


@pytest.fixture(scope="module", autouse=True)
def image_data_row_factory():
    def image_data_row(global_key):
        return {
            "row_data": "https://lb-test-data.s3.us-west-1.amazonaws.com/image-samples/sample-image-1.jpg",
            "global_key": f"https://lb-test-data.s3.us-west-1.amazonaws.com/image-samples/sample-image-1.jpg-{global_key}",
            "media_type": "IMAGE",
        }

    return image_data_row


@pytest.fixture(scope="module", autouse=True)
def document_data_row_factory():
    def document_data_row(global_key):
        return {
            "row_data": {
                "pdf_url": "https://storage.googleapis.com/labelbox-datasets/arxiv-pdf/data/99-word-token-pdfs/0801.3483.pdf",
                "text_layer_url": "https://storage.googleapis.com/labelbox-datasets/arxiv-pdf/data/99-word-token-pdfs/0801.3483-lb-textlayer.json",
            },
            "global_key": f"https://storage.googleapis.com/labelbox-datasets/arxiv-pdf/data/99-word-token-pdfs/0801.3483.pdf-{global_key}",
            "media_type": "PDF",
        }

    return document_data_row


@pytest.fixture(scope="module", autouse=True)
def text_data_row_factory():
    def text_data_row(global_key):
        return {
            "row_data": "https://storage.googleapis.com/lb-artifacts-testing-public/sdk_integration_test/sample-text-2.txt",
            "global_key": f"https://storage.googleapis.com/lb-artifacts-testing-public/sdk_integration_test/sample-text-2.txt-{global_key}",
            "media_type": "TEXT",
        }

    return text_data_row


@pytest.fixture(scope="module", autouse=True)
def llm_human_preference_data_row_factory():
    def llm_human_preference_data_row(global_key):
        return {
            "row_data": "https://storage.googleapis.com/labelbox-datasets/sdk_test/llm_prompt_response_conv.json",
            "global_key": global_key,
        }

    return llm_human_preference_data_row


@pytest.fixture(scope="module")
def mmc_data_row_url():
    return "https://storage.googleapis.com/labelbox-datasets/conversational_model_evaluation_sample/offline-model-chat-evaluation.json"


@pytest.fixture(scope="module", autouse=True)
def offline_model_evaluation_data_row_factory(mmc_data_row_url: str):
    def offline_model_evaluation_data_row(global_key: str):
        return {
            "row_data": mmc_data_row_url,
            "global_key": global_key,
        }

    return offline_model_evaluation_data_row


@pytest.fixture(scope="module", autouse=True)
def data_row_json_by_media_type(
    audio_data_row_factory,
    conversational_data_row_factory,
    dicom_data_row_factory,
    geospatial_data_row_factory,
    html_data_row_factory,
    image_data_row_factory,
    document_data_row_factory,
    text_data_row_factory,
    video_data_row_factory,
    offline_model_evaluation_data_row_factory,
):
    return {
        MediaType.Audio: audio_data_row_factory,
        MediaType.Conversational: conversational_data_row_factory,
        MediaType.Dicom: dicom_data_row_factory,
        MediaType.Geospatial_Tile: geospatial_data_row_factory,
        MediaType.Html: html_data_row_factory,
        MediaType.Image: image_data_row_factory,
        MediaType.Document: document_data_row_factory,
        MediaType.Text: text_data_row_factory,
        MediaType.Video: video_data_row_factory,
        OntologyKind.ModelEvaluation: offline_model_evaluation_data_row_factory,
    }


@pytest.fixture(scope="module", autouse=True)
def normalized_ontology_by_media_type():
    """Returns NDJSON of ontology based on media type"""

    bbox_tool_with_nested_text = {
        "required": False,
        "name": "bbox_tool_with_nested_text",
        "tool": "rectangle",
        "color": "#a23030",
        "classifications": [
            {
                "required": False,
                "instructions": "nested",
                "name": "nested",
                "type": "radio",
                "options": [
                    {
                        "label": "radio_value_1",
                        "value": "radio_value_1",
                        "options": [
                            {
                                "required": False,
                                "instructions": "nested_checkbox",
                                "name": "nested_checkbox",
                                "type": "checklist",
                                "options": [
                                    {
                                        "label": "nested_checkbox_option_1",
                                        "value": "nested_checkbox_option_1",
                                        "options": [],
                                    },
                                    {
                                        "label": "nested_checkbox_option_2",
                                        "value": "nested_checkbox_option_2",
                                    },
                                ],
                            },
                            {
                                "required": False,
                                "instructions": "nested_text",
                                "name": "nested_text",
                                "type": "text",
                                "options": [],
                            },
                        ],
                    },
                ],
            }
        ],
    }

    bbox_tool = {
        "required": False,
        "name": "bbox",
        "tool": "rectangle",
        "color": "#a23030",
        "classifications": [],
    }

    polygon_tool = {
        "required": False,
        "name": "polygon",
        "tool": "polygon",
        "color": "#FF34FF",
        "classifications": [],
    }
    polyline_tool = {
        "required": False,
        "name": "polyline",
        "tool": "line",
        "color": "#FF4A46",
        "classifications": [],
    }
    point_tool = {
        "required": False,
        "name": "point--",
        "tool": "point",
        "color": "#008941",
        "classifications": [],
    }
    entity_tool = {
        "required": False,
        "name": "named-entity",
        "tool": "named-entity",
        "color": "#006FA6",
        "classifications": [],
    }
    raster_segmentation_tool = {
        "required": False,
        "name": "segmentation_mask",
        "tool": "raster-segmentation",
        "color": "#ff0000",
        "classifications": [],
    }
    segmentation_tool = {
        "required": False,
        "name": "segmentation--",
        "tool": "superpixel",
        "color": "#A30059",
        "classifications": [],
    }
    checklist = {
        "required": False,
        "instructions": "checklist",
        "name": "checklist",
        "type": "checklist",
        "options": [
            {
                "label": "first_checklist_answer",
                "value": "first_checklist_answer",
            },
            {
                "label": "second_checklist_answer",
                "value": "second_checklist_answer",
            },
        ],
    }
    checklist_index = {
        "required": False,
        "instructions": "checklist_index",
        "name": "checklist_index",
        "type": "checklist",
        "scope": "index",
        "options": [
            {
                "label": "first_checklist_answer",
                "value": "first_checklist_answer",
            },
            {
                "label": "second_checklist_answer",
                "value": "second_checklist_answer",
            },
        ],
    }
    free_form_text = {
        "required": False,
        "instructions": "text",
        "name": "text",
        "type": "text",
        "options": [],
    }
    free_form_text_index = {
        "required": False,
        "instructions": "text_index",
        "name": "text_index",
        "type": "text",
        "scope": "index",
        "options": [],
    }
    radio = {
        "required": False,
        "instructions": "radio",
        "name": "radio",
        "type": "radio",
        "options": [
            {
                "label": "first_radio_answer",
                "value": "first_radio_answer",
                "options": [],
            },
            {
                "label": "second_radio_answer",
                "value": "second_radio_answer",
                "options": [],
            },
        ],
    }

    radio_index = {
        "required": False,
        "instructions": "radio_index",
        "name": "radio_index",
        "type": "radio",
        "scope": "index",
        "options": [
            {
                "label": "first_radio_answer",
                "value": "first_radio_answer",
                "options": [],
            },
            {
                "label": "second_radio_answer",
                "value": "second_radio_answer",
                "options": [],
            },
        ],
    }

    prompt_text = {
        "instructions": "prompt-text",
        "name": "prompt-text",
        "options": [],
        "required": True,
        "maxCharacters": 50,
        "minCharacters": 1,
        "schemaNodeId": None,
        "type": "prompt",
    }

    response_radio = {
        "instructions": "radio-response",
        "name": "radio-response",
        "options": [
            {
                "label": "first_radio_answer",
                "value": "first_radio_answer",
                "options": [],
            },
            {
                "label": "second_radio_answer",
                "value": "second_radio_answer",
                "options": [],
            },
        ],
        "required": True,
        "type": "response-radio",
    }

    response_checklist = {
        "instructions": "checklist-response",
        "name": "checklist-response",
        "options": [
            {
                "label": "first_checklist_answer",
                "value": "first_checklist_answer",
                "options": [],
            },
            {
                "label": "second_checklist_answer",
                "value": "second_checklist_answer",
                "options": [],
            },
        ],
        "required": True,
        "type": "response-checklist",
    }

    response_text = {
        "instructions": "response-text",
        "maxCharacters": 20,
        "minCharacters": 1,
        "name": "response-text",
        "required": True,
        "type": "response-text",
    }

    message_single_selection_task = {
        "required": False,
        "name": "message-single-selection",
        "tool": "message-single-selection",
        "classifications": [],
    }

    message_multi_selection_task = {
        "required": False,
        "name": "message-multi-selection",
        "tool": "message-multi-selection",
        "classifications": [],
    }

    message_ranking_task = {
        "required": False,
        "name": "message-ranking",
        "tool": "message-ranking",
        "classifications": [],
    }

    return {
        MediaType.Image: {
            "tools": [
                bbox_tool,
                bbox_tool_with_nested_text,
                polygon_tool,
                polyline_tool,
                point_tool,
                raster_segmentation_tool,
            ],
            "classifications": [
                checklist,
                free_form_text,
                radio,
            ],
        },
        MediaType.Text: {
            "tools": [entity_tool],
            "classifications": [
                checklist,
                free_form_text,
                radio,
            ],
        },
        MediaType.Video: {
            "tools": [
                bbox_tool,
                bbox_tool_with_nested_text,
                polyline_tool,
                point_tool,
                raster_segmentation_tool,
            ],
            "classifications": [
                checklist,
                free_form_text,
                radio,
                checklist_index,
                free_form_text_index,
            ],
        },
        MediaType.Geospatial_Tile: {
            "tools": [
                bbox_tool,
                bbox_tool_with_nested_text,
                polygon_tool,
                polyline_tool,
                point_tool,
            ],
            "classifications": [
                checklist,
                free_form_text,
                radio,
            ],
        },
        MediaType.Document: {
            "tools": [entity_tool, bbox_tool, bbox_tool_with_nested_text],
            "classifications": [
                checklist,
                free_form_text,
                radio,
            ],
        },
        MediaType.Audio: {
            "tools": [],
            "classifications": [
                checklist,
                free_form_text,
                radio,
            ],
        },
        MediaType.Html: {
            "tools": [],
            "classifications": [
                checklist,
                free_form_text,
                radio,
            ],
        },
        MediaType.Dicom: {
            "tools": [raster_segmentation_tool, polyline_tool],
            "classifications": [],
        },
        MediaType.Conversational: {
            "tools": [entity_tool],
            "classifications": [
                checklist,
                free_form_text,
                radio,
                checklist_index,
                free_form_text_index,
            ],
        },
        MediaType.LLMPromptResponseCreation: {
            "tools": [],
            "classifications": [
                prompt_text,
                response_text,
                response_radio,
                response_checklist,
            ],
        },
        MediaType.LLMPromptCreation: {
            "tools": [],
            "classifications": [prompt_text],
        },
        OntologyKind.ResponseCreation: {
            "tools": [],
            "classifications": [
                response_text,
                response_radio,
                response_checklist,
            ],
        },
        OntologyKind.ModelEvaluation: {
            "tools": [
                message_single_selection_task,
                message_multi_selection_task,
                message_ranking_task,
            ],
            "classifications": [
                radio,
                checklist,
                free_form_text,
                radio_index,
                checklist_index,
                free_form_text_index,
            ],
        },
        "all": {
            "tools": [
                bbox_tool,
                bbox_tool_with_nested_text,
                polygon_tool,
                polyline_tool,
                point_tool,
                entity_tool,
                segmentation_tool,
                raster_segmentation_tool,
            ],
            "classifications": [
                checklist,
                checklist_index,
                free_form_text,
                free_form_text_index,
                radio,
            ],
        },
    }


@pytest.fixture
def wait_for_label_processing():
    """
    Do not use. Only for testing.

    Returns project's labels as a list after waiting for them to finish processing.
    If `project.labels()` is called before label is fully processed,
    it may return an empty set
    """

    def func(project):
        timeout_seconds = 10
        while True:
            labels = list(project.labels())
            if len(labels) > 0:
                return labels
            timeout_seconds -= 2
            if timeout_seconds <= 0:
                raise TimeoutError(
                    f"Timed out waiting for label for project '{project.uid}' to finish processing"
                )
            time.sleep(2)

    return func


##### Unit test strategies #####


@pytest.fixture
def hardcoded_datarow_id():
    data_row_id = "ck8q9q9qj00003g5z3q1q9q9q"

    def get_data_row_id():
        return data_row_id

    yield get_data_row_id


@pytest.fixture
def hardcoded_global_key():
    global_key = str(uuid.uuid4())

    def get_global_key():
        return global_key

    yield get_global_key


##### Integration test strategies #####


def _create_response_creation_project(
    client: Client,
    rand_gen,
    data_row_json_by_media_type,
    ontology_kind,
    normalized_ontology_by_media_type,
) -> Tuple[Project, Ontology, Dataset]:
    "For response creation projects"

    dataset = client.create_dataset(name=rand_gen(str))

    project = client.create_response_creation_project(
        name=f"{ontology_kind}-{rand_gen(str)}"
    )

    ontology = client.create_ontology(
        name=f"{ontology_kind}-{rand_gen(str)}",
        normalized=normalized_ontology_by_media_type[ontology_kind],
        media_type=MediaType.Text,
        ontology_kind=ontology_kind,
    )

    project.connect_ontology(ontology)

    data_row_data = []

    for _ in range(DATA_ROW_COUNT):
        data_row_data.append(
            data_row_json_by_media_type[MediaType.Text](rand_gen(str))
        )

    task = dataset.create_data_rows(data_row_data)
    task.wait_till_done()
    global_keys = [row["global_key"] for row in task.result]
    data_row_ids = [row["id"] for row in task.result]

    project.create_batch(
        rand_gen(str),
        data_row_ids,  # sample of data row objects
        5,  # priority between 1(Highest) - 5(lowest)
    )
    project.data_row_ids = data_row_ids
    project.global_keys = global_keys

    return project, ontology, dataset


@pytest.fixture
def llm_prompt_response_creation_dataset_with_data_row(
    client: Client, rand_gen
):
    dataset = client.create_dataset(name=rand_gen(str))
    global_key = str(uuid.uuid4())

    convo_data = {
        "row_data": "https://storage.googleapis.com/labelbox-datasets/conversational-sample-data/pairwise_shopping_2.json",
        "global_key": global_key,
    }

    task = dataset.create_data_rows([convo_data])
    task.wait_till_done()
    assert task.status == "COMPLETE"
    yield dataset

    dataset.delete()


def _create_prompt_response_project(
    client: Client,
    rand_gen,
    media_type,
    normalized_ontology_by_media_type,
    export_v2_test_helpers,
    llm_prompt_response_creation_dataset_with_data_row,
) -> Tuple[Project, Ontology]:
    """For prompt response data row auto gen projects"""
    dataset = llm_prompt_response_creation_dataset_with_data_row
    prompt_response_project = client.create_prompt_response_generation_project(
        name=f"{media_type.value}-{rand_gen(str)}",
        dataset_id=dataset.uid,
        media_type=media_type,
    )

    ontology = client.create_ontology(
        name=f"{media_type}-{rand_gen(str)}",
        normalized=normalized_ontology_by_media_type[media_type],
        media_type=media_type,
    )

    prompt_response_project.connect_ontology(ontology)

    # We have to export to get data row ids
    result = export_v2_test_helpers.run_project_export_v2_task(
        prompt_response_project
    )

    data_row_ids = [dr["data_row"]["id"] for dr in result]
    global_keys = [dr["data_row"]["global_key"] for dr in result]

    prompt_response_project.data_row_ids = data_row_ids
    prompt_response_project.global_keys = global_keys

    return prompt_response_project, ontology


def _create_offline_mmc_project(
    client: Client, rand_gen, data_row_json, normalized_ontology
) -> Tuple[Project, Ontology, Dataset]:
    dataset = client.create_dataset(name=rand_gen(str))

    project = client.create_offline_model_evaluation_project(
        name=f"offline-mmc-{rand_gen(str)}",
    )

    ontology = client.create_ontology(
        name=f"offline-mmc-{rand_gen(str)}",
        normalized=normalized_ontology,
        media_type=MediaType.Conversational,
        ontology_kind=OntologyKind.ModelEvaluation,
    )

    project.connect_ontology(ontology)

    data_row_data = [
        data_row_json(rand_gen(str)) for _ in range(DATA_ROW_COUNT)
    ]

    task = dataset.create_data_rows(data_row_data)
    task.wait_till_done()
    global_keys = [row["global_key"] for row in task.result]
    data_row_ids = [row["id"] for row in task.result]

    project.create_batch(
        rand_gen(str),
        data_row_ids,  # sample of data row objects
        5,  # priority between 1(Highest) - 5(lowest)
    )
    project.data_row_ids = data_row_ids
    project.data_row_data = data_row_data
    project.global_keys = global_keys

    return project, ontology, dataset


def _create_project(
    client: Client,
    rand_gen,
    data_row_json_by_media_type,
    media_type,
    normalized_ontology_by_media_type,
) -> Tuple[Project, Ontology, Dataset]:
    """Shared function to configure project for integration tests"""

    dataset = client.create_dataset(name=rand_gen(str))

    project = client.create_project(
        name=f"{media_type}-{rand_gen(str)}", media_type=media_type
    )

    ontology = client.create_ontology(
        name=f"{media_type}-{rand_gen(str)}",
        normalized=normalized_ontology_by_media_type[media_type],
        media_type=media_type,
    )

    project.connect_ontology(ontology)
    data_row_data = []

    for _ in range(DATA_ROW_COUNT):
        data_row_data.append(
            data_row_json_by_media_type[media_type](rand_gen(str))
        )

    task = dataset.create_data_rows(data_row_data)
    task.wait_till_done()
    global_keys = [row["global_key"] for row in task.result]
    data_row_ids = [row["id"] for row in task.result]

    project.create_batch(
        rand_gen(str),
        data_row_ids,  # sample of data row objects
        5,  # priority between 1(Highest) - 5(lowest)
    )
    project.data_row_ids = data_row_ids
    project.global_keys = global_keys

    return project, ontology, dataset


@pytest.fixture
def configured_project(
    client: Client,
    rand_gen,
    data_row_json_by_media_type,
    request: FixtureRequest,
    normalized_ontology_by_media_type,
    export_v2_test_helpers,
    llm_prompt_response_creation_dataset_with_data_row,
    teardown_helpers,
):
    """Configure project for test. Request.param will contain the media type if not present will use Image MediaType. The project will have 10 data rows."""

    media_type: Union[MediaType, OntologyKind] = getattr(
        request, "param", MediaType.Image
    )

    dataset = None

    if (
        media_type == MediaType.LLMPromptCreation
        or media_type == MediaType.LLMPromptResponseCreation
    ):
        project, ontology = _create_prompt_response_project(
            client,
            rand_gen,
            media_type,
            normalized_ontology_by_media_type,
            export_v2_test_helpers,
            llm_prompt_response_creation_dataset_with_data_row,
        )
    elif media_type == OntologyKind.ResponseCreation:
        project, ontology, dataset = _create_response_creation_project(
            client,
            rand_gen,
            data_row_json_by_media_type,
            media_type,
            normalized_ontology_by_media_type,
        )
    elif media_type == OntologyKind.ModelEvaluation:
        project, ontology, dataset = _create_offline_mmc_project(
            client,
            rand_gen,
            data_row_json_by_media_type[media_type],
            normalized_ontology_by_media_type[media_type],
        )
    else:
        project, ontology, dataset = _create_project(
            client,
            rand_gen,
            data_row_json_by_media_type,
            media_type,
            normalized_ontology_by_media_type,
        )

    yield project

    teardown_helpers.teardown_project_labels_ontology_feature_schemas(project)

    if dataset:
        dataset.delete()


@pytest.fixture()
def configured_project_by_global_key(
    client: Client,
    rand_gen,
    data_row_json_by_media_type,
    request: FixtureRequest,
    normalized_ontology_by_media_type,
    export_v2_test_helpers,
    teardown_helpers,
):
    """Does the same thing as configured project but with global keys focus."""

    media_type = getattr(request, "param", MediaType.Image)
    dataset = None

    if (
        media_type == MediaType.LLMPromptCreation
        or media_type == MediaType.LLMPromptResponseCreation
    ):
        project, ontology = _create_prompt_response_project(
            client,
            rand_gen,
            media_type,
            normalized_ontology_by_media_type,
            export_v2_test_helpers,
        )
    elif media_type == OntologyKind.ResponseCreation:
        project, ontology, dataset = _create_response_creation_project(
            client,
            rand_gen,
            data_row_json_by_media_type,
            media_type,
            normalized_ontology_by_media_type,
        )
    elif media_type == OntologyKind.ModelEvaluation:
        project, ontology, dataset = _create_offline_mmc_project(
            client,
            rand_gen,
            data_row_json_by_media_type[media_type],
            normalized_ontology_by_media_type[media_type],
        )
    else:
        project, ontology, dataset = _create_project(
            client,
            rand_gen,
            data_row_json_by_media_type,
            media_type,
            normalized_ontology_by_media_type,
        )

    yield project

    teardown_helpers.teardown_project_labels_ontology_feature_schemas(project)

    if dataset:
        dataset.delete()


@pytest.fixture(scope="module")
def module_project(
    client: Client,
    rand_gen,
    data_row_json_by_media_type,
    request: FixtureRequest,
    normalized_ontology_by_media_type,
    module_teardown_helpers,
):
    """Generates a image project that scopes to the test module(file). Used to reduce api calls."""

    media_type = getattr(request, "param", MediaType.Image)
    media_type = getattr(request, "param", MediaType.Image)
    dataset = None

    if (
        media_type == MediaType.LLMPromptCreation
        or media_type == MediaType.LLMPromptResponseCreation
    ):
        project, ontology = _create_prompt_response_project(
            client, rand_gen, media_type, normalized_ontology_by_media_type
        )
    elif media_type == OntologyKind.ResponseCreation:
        project, ontology, dataset = _create_response_creation_project(
            client,
            rand_gen,
            data_row_json_by_media_type,
            media_type,
            normalized_ontology_by_media_type,
        )
    else:
        project, ontology, dataset = _create_project(
            client,
            rand_gen,
            data_row_json_by_media_type,
            media_type,
            normalized_ontology_by_media_type,
        )

    yield project

    module_teardown_helpers.teardown_project_labels_ontology_feature_schemas(
        project
    )

    if dataset:
        dataset.delete()


@pytest.fixture
def prediction_id_mapping(request, normalized_ontology_by_media_type):
    """Creates the base of annotation based on tools inside project ontology. We would want only annotations supported for the MediaType of the ontology and project. Annotations are generated for each data row created later be combined inside the test file. This serves as the base fixture for all the interference (annotations) fixture. This fixtures supports a few strategies:

    Integration test:
        configured_project: generates data rows with data row id focus.
        configured_project_by_global_key: generates data rows with global key focus.
        module_configured_project: configured project but scoped to test module.

    Unit tests
        Individuals can supply hard-coded data row ids or global keys without configured a project must include a media type fixture to get the appropriate annotations.

    Each strategy provides a few items.

        Labelbox Project (unit testing strategies do not make api calls so will have None for project)
        Data row identifiers (ids the annotation uses)
        Ontology: normalized ontology
    """

    if "configured_project" in request.fixturenames:
        project = request.getfixturevalue("configured_project")
        data_row_identifiers = [
            {"id": data_row_id} for data_row_id in project.data_row_ids
        ]
        ontology = project.ontology().normalized

    elif "configured_project_by_global_key" in request.fixturenames:
        project = request.getfixturevalue("configured_project_by_global_key")
        data_row_identifiers = [
            {"globalKey": global_key} for global_key in project.global_keys
        ]
        ontology = project.ontology().normalized

    elif "module_project" in request.fixturenames:
        project = request.getfixturevalue("module_project")
        data_row_identifiers = [
            {"id": data_row_id} for data_row_id in project.data_row_ids
        ]
        ontology = project.ontology().normalized

    elif "hardcoded_datarow_id" in request.fixturenames:
        if "media_type" not in request.fixturenames:
            raise Exception("Please include a 'media_type' fixture")
        project = None
        media_type = request.getfixturevalue("media_type")
        ontology = normalized_ontology_by_media_type[media_type]
        data_row_identifiers = [
            {"id": request.getfixturevalue("hardcoded_datarow_id")()}
        ]

    elif "hardcoded_global_key" in request.fixturenames:
        if "media_type" not in request.fixturenames:
            raise Exception("Please include a 'media_type' fixture")
        project = None
        media_type = request.getfixturevalue("media_type")
        ontology = normalized_ontology_by_media_type[media_type]
        data_row_identifiers = [
            {"globalKey": request.getfixturevalue("hardcoded_global_key")()}
        ]

    # Used for tests that need access to every ontology
    else:
        project = None
        media_type = None
        ontology = normalized_ontology_by_media_type["all"]
        data_row_identifiers = [{"id": "ck8q9q9qj00003g5z3q1q9q9q"}]

    base_annotations = []
    for data_row_identifier in data_row_identifiers:
        base_annotation = {}
        for feature in ontology["tools"] + ontology["classifications"]:
            if "tool" in feature:
                feature_type = (
                    feature["tool"]
                    if feature["classifications"] == []
                    else f"{feature['tool']}_nested"
                )  # tool vs nested classification tool
            else:
                feature_type = (
                    feature["type"]
                    if "scope" not in feature
                    else f"{feature['type']}_{feature['scope']}"
                )  # checklist vs indexed checklist

            base_annotation[feature_type] = {
                "uuid": str(uuid.uuid4()),
                "name": feature["name"],
                "tool": feature,
                "dataRow": data_row_identifier,
            }

        base_annotations.append(base_annotation)
    return base_annotations


@pytest.fixture
def mmc_example_data_row_message_ids(mmc_data_row_url: str):
    data_row_content = requests.get(mmc_data_row_url).json()

    human_id = next(
        actor_id
        for actor_id, actor_metadata in data_row_content["actors"].items()
        if actor_metadata["role"] == "human"
    )

    return {
        message_id: [
            {
                "id": child_msg_id,
                "model_config_name": data_row_content["actors"][
                    data_row_content["messages"][child_msg_id]["actorId"]
                ]["metadata"]["modelConfigName"],
            }
            for child_msg_id in message_metadata["childMessageIds"]
        ]
        for message_id, message_metadata in data_row_content["messages"].items()
        if message_metadata["actorId"] == human_id
    }


# Each inference represents a feature type that adds to the base annotation created with prediction_id_mapping
@pytest.fixture
def polygon_inference(prediction_id_mapping):
    polygons = []
    for feature in prediction_id_mapping:
        if "polygon" not in feature:
            continue
        polygon = feature["polygon"].copy()
        polygon.update(
            {
                "polygon": [
                    {"x": 147.692, "y": 118.154},
                    {"x": 142.769, "y": 104.923},
                    {"x": 57.846, "y": 118.769},
                    {"x": 28.308, "y": 169.846},
                ]
            }
        )
        del polygon["tool"]
        polygons.append(polygon)
    return polygons


@pytest.fixture
def rectangle_inference(prediction_id_mapping):
    rectangles = []
    for feature in prediction_id_mapping:
        if "rectangle" not in feature:
            continue
        rectangle = feature["rectangle"].copy()
        rectangle.update(
            {
                "bbox": {"top": 48, "left": 58, "height": 65, "width": 12},
            }
        )
        del rectangle["tool"]
        rectangles.append(rectangle)
    return rectangles


@pytest.fixture
def rectangle_inference_with_confidence(prediction_id_mapping):
    rectangles = []
    for feature in prediction_id_mapping:
        if "rectangle_nested" not in feature:
            continue
        rectangle = feature["rectangle_nested"].copy()
        rectangle.update(
            {
                "bbox": {"top": 48, "left": 58, "height": 65, "width": 12},
                "classifications": [
                    {
                        "name": rectangle["tool"]["classifications"][0]["name"],
                        "answer": {
                            "name": rectangle["tool"]["classifications"][0][
                                "options"
                            ][0]["value"],
                            "classifications": [
                                {
                                    "name": rectangle["tool"][
                                        "classifications"
                                    ][0]["options"][0]["options"][1]["name"],
                                    "answer": "nested answer",
                                }
                            ],
                        },
                    }
                ],
            }
        )

        rectangle.update({"confidence": 0.9})
        rectangle["classifications"][0]["answer"]["confidence"] = 0.8
        rectangle["classifications"][0]["answer"]["classifications"][0][
            "confidence"
        ] = 0.7

        del rectangle["tool"]
        rectangles.append(rectangle)
    return rectangles


@pytest.fixture
def rectangle_inference_document(rectangle_inference):
    rectangles = []
    for feature in rectangle_inference:
        rectangle = feature.copy()
        rectangle.update({"page": 1, "unit": "POINTS"})
        rectangles.append(rectangle)
    return rectangles


@pytest.fixture
def line_inference(prediction_id_mapping):
    lines = []
    for feature in prediction_id_mapping:
        if "line" not in feature:
            continue
        line = feature["line"].copy()
        line.update(
            {
                "line": [
                    {"x": 147.692, "y": 118.154},
                    {"x": 150.692, "y": 160.154},
                ]
            }
        )
        del line["tool"]
        lines.append(line)
    return lines


@pytest.fixture
def line_inference_v2(prediction_id_mapping):
    lines = []
    for feature in prediction_id_mapping:
        if "line" not in feature:
            continue
        line = feature["line"].copy()
        line_data = {
            "groupKey": "axial",
            "segments": [
                {
                    "keyframes": [
                        {
                            "frame": 1,
                            "line": [
                                {"x": 147.692, "y": 118.154},
                                {"x": 150.692, "y": 160.154},
                            ],
                        }
                    ]
                },
            ],
        }
        line.update(line_data)
        del line["tool"]
        lines.append(line)
    return lines


@pytest.fixture
def point_inference(prediction_id_mapping):
    points = []
    for feature in prediction_id_mapping:
        if "point" not in feature:
            continue
        point = feature["point"].copy()
        point.update({"point": {"x": 147.692, "y": 118.154}})
        del point["tool"]
        points.append(point)
    return points


@pytest.fixture
def entity_inference(prediction_id_mapping):
    named_entities = []
    for feature in prediction_id_mapping:
        if "named-entity" not in feature:
            continue
        entity = feature["named-entity"].copy()
        entity.update({"location": {"start": 112, "end": 128}})
        del entity["tool"]
        named_entities.append(entity)
    return named_entities


@pytest.fixture
def entity_inference_index(prediction_id_mapping):
    named_entities = []
    for feature in prediction_id_mapping:
        if "named-entity" not in feature:
            continue
        entity = feature["named-entity"].copy()
        entity.update(
            {
                "location": {"start": 0, "end": 8},
                "messageId": "0",
            }
        )
        del entity["tool"]
        named_entities.append(entity)
    return named_entities


@pytest.fixture
def entity_inference_document(prediction_id_mapping):
    named_entities = []
    for feature in prediction_id_mapping:
        if "named-entity" not in feature:
            continue
        entity = feature["named-entity"].copy()
        document_selections = {
            "textSelections": [
                {
                    "tokenIds": [
                        "3f984bf3-1d61-44f5-b59a-9658a2e3440f",
                        "3bf00b56-ff12-4e52-8cc1-08dbddb3c3b8",
                        "6e1c3420-d4b7-4c5a-8fd6-ead43bf73d80",
                        "87a43d32-af76-4a1d-b262-5c5f4d5ace3a",
                        "e8606e8a-dfd9-4c49-a635-ad5c879c75d0",
                        "67c7c19e-4654-425d-bf17-2adb8cf02c30",
                        "149c5e80-3e07-49a7-ab2d-29ddfe6a38fa",
                        "b0e94071-2187-461e-8e76-96c58738a52c",
                    ],
                    "groupId": "2f4336f4-a07e-4e0a-a9e1-5629b03b719b",
                    "page": 1,
                }
            ]
        }
        entity.update(document_selections)
        del entity["tool"]
        named_entities.append(entity)
    return named_entities


@pytest.fixture
def segmentation_inference(prediction_id_mapping):
    superpixel_masks = []
    for feature in prediction_id_mapping:
        if "superpixel" not in feature:
            continue
        segmentation = feature["superpixel"].copy()
        segmentation.update(
            {
                "mask": {
                    "instanceURI": "https://storage.googleapis.com/labelbox-datasets/image_sample_data/raster_seg.png",
                    "colorRGB": (255, 255, 255),
                }
            }
        )
        del segmentation["tool"]
        superpixel_masks.append(segmentation)
    return superpixel_masks


@pytest.fixture
def segmentation_inference_rle(prediction_id_mapping):
    superpixel_masks = []
    for feature in prediction_id_mapping:
        if "superpixel" not in feature:
            continue
        segmentation = feature["superpixel"].copy()
        segmentation.update(
            {
                "uuid": str(uuid.uuid4()),
                "mask": {"size": [10, 10], "counts": [1, 0, 10, 100]},
            }
        )
        del segmentation["tool"]
        superpixel_masks.append(segmentation)
    return superpixel_masks


@pytest.fixture
def segmentation_inference_png(prediction_id_mapping):
    superpixel_masks = []
    for feature in prediction_id_mapping:
        if "superpixel" not in feature:
            continue
        segmentation = feature["superpixel"].copy()
        segmentation.update(
            {
                "uuid": str(uuid.uuid4()),
                "mask": {
                    "png": "somedata",
                },
            }
        )
        del segmentation["tool"]
        superpixel_masks.append(segmentation)
    return superpixel_masks


@pytest.fixture
def checklist_inference(prediction_id_mapping):
    checklists = []
    for feature in prediction_id_mapping:
        if "checklist" not in feature:
            continue
        checklist = feature["checklist"].copy()
        checklist.update(
            {
                "answers": [
                    {"name": "first_checklist_answer"},
                    {"name": "second_checklist_answer"},
                ]
            }
        )
        del checklist["tool"]
        checklists.append(checklist)
    return checklists


@pytest.fixture
def checklist_inference_index(prediction_id_mapping):
    checklists = []
    for feature in prediction_id_mapping:
        if "checklist_index" not in feature:
            return None
        checklist = feature["checklist_index"].copy()
        checklist.update(
            {
                "answers": [
                    {"name": "first_checklist_answer"},
                    {"name": "second_checklist_answer"},
                ],
                "messageId": "0",
            }
        )
        del checklist["tool"]
        checklists.append(checklist)
    return checklists


@pytest.fixture
def checklist_inference_index_mmc(
    prediction_id_mapping, mmc_example_data_row_message_ids
):
    checklists = []
    for feature in prediction_id_mapping:
        if "checklist_index" not in feature:
            return None
        checklist = feature["checklist_index"].copy()
        checklist.update(
            {
                "answers": [
                    {"name": "first_checklist_answer"},
                    {"name": "second_checklist_answer"},
                ],
                "messageId": next(
                    iter(mmc_example_data_row_message_ids.keys())
                ),
            }
        )
        del checklist["tool"]
        checklists.append(checklist)
    return checklists


@pytest.fixture
def prompt_text_inference(prediction_id_mapping):
    prompt_texts = []
    for feature in prediction_id_mapping:
        if "prompt" not in feature:
            continue
        text = feature["prompt"].copy()
        text.update({"answer": "free form text..."})
        del text["tool"]
        prompt_texts.append(text)
    return prompt_texts


@pytest.fixture
def radio_response_inference(prediction_id_mapping):
    response_radios = []
    for feature in prediction_id_mapping:
        if "response-radio" not in feature:
            continue
        response_radio = feature["response-radio"].copy()
        response_radio.update(
            {
                "answer": {"name": "first_radio_answer"},
            }
        )
        del response_radio["tool"]
        response_radios.append(response_radio)
    return response_radios


@pytest.fixture
def radio_inference(prediction_id_mapping):
    radios = []
    for feature in prediction_id_mapping:
        if "radio" not in feature:
            continue
        radio = feature["radio"].copy()
        radio.update(
            {
                "answer": {"name": "first_radio_answer"},
            }
        )
        del radio["tool"]
        radios.append(radio)
    return radios


@pytest.fixture
def radio_inference_index_mmc(
    prediction_id_mapping, mmc_example_data_row_message_ids
):
    radios = []
    for feature in prediction_id_mapping:
        if "radio_index" not in feature:
            continue
        radio = feature["radio_index"].copy()
        radio.update(
            {
                "answer": {"name": "first_radio_answer"},
                "messageId": next(
                    iter(mmc_example_data_row_message_ids.keys())
                ),
            }
        )
        del radio["tool"]
        radios.append(radio)
    return radios


@pytest.fixture
def checklist_response_inference(prediction_id_mapping):
    response_checklists = []
    for feature in prediction_id_mapping:
        if "response-checklist" not in feature:
            continue
        response_checklist = feature["response-checklist"].copy()
        response_checklist.update(
            {
                "answer": [
                    {"name": "first_checklist_answer"},
                    {"name": "second_checklist_answer"},
                ]
            }
        )
        del response_checklist["tool"]
        response_checklists.append(response_checklist)
    return response_checklists


@pytest.fixture
def text_response_inference(prediction_id_mapping):
    response_texts = []
    for feature in prediction_id_mapping:
        if "response-text" not in feature:
            continue
        text = feature["response-text"].copy()
        text.update({"answer": "free form text..."})
        del text["tool"]
        response_texts.append(text)
    return response_texts


@pytest.fixture
def text_inference(prediction_id_mapping):
    texts = []
    for feature in prediction_id_mapping:
        if "text" not in feature:
            continue
        text = feature["text"].copy()
        text.update({"answer": "free form text..."})
        del text["tool"]
        texts.append(text)
    return texts


@pytest.fixture
def text_inference_with_confidence(text_inference):
    texts = []
    for feature in text_inference:
        text = feature.copy()
        text.update({"confidence": 0.9})
        texts.append(text)
    return texts


@pytest.fixture
def text_inference_index(prediction_id_mapping):
    texts = []
    for feature in prediction_id_mapping:
        if "text_index" not in feature:
            continue
        text = feature["text_index"].copy()
        text.update({"answer": "free form text...", "messageId": "0"})
        del text["tool"]
        texts.append(text)
    return texts


@pytest.fixture
def text_inference_index_mmc(
    prediction_id_mapping, mmc_example_data_row_message_ids
):
    texts = []
    for feature in prediction_id_mapping:
        if "text_index" not in feature:
            continue
        text = feature["text_index"].copy()
        text.update(
            {
                "answer": "free form text...",
                "messageId": next(
                    iter(mmc_example_data_row_message_ids.keys())
                ),
            }
        )
        del text["tool"]
        texts.append(text)
    return texts


@pytest.fixture
def video_checklist_inference(prediction_id_mapping):
    checklists = []
    for feature in prediction_id_mapping:
        if "checklist" not in feature:
            continue
        checklist = feature["checklist"].copy()
        checklist.update(
            {
                "answers": [
                    {"name": "first_checklist_answer"},
                    {"name": "second_checklist_answer"},
                ]
            }
        )

        checklist.update(
            {
                "frames": [
                    {
                        "start": 7,
                        "end": 13,
                    },
                    {
                        "start": 18,
                        "end": 19,
                    },
                ]
            }
        )
        del checklist["tool"]
        checklists.append(checklist)
    return checklists


@pytest.fixture
def message_single_selection_inference(
    prediction_id_mapping, mmc_example_data_row_message_ids
):
    some_parent_id, some_child_ids = next(
        iter(mmc_example_data_row_message_ids.items())
    )

    res = []
    for feature in prediction_id_mapping:
        if "message-single-selection" not in feature:
            continue
        selection = feature["message-single-selection"].copy()
        selection.update(
            {
                "messageEvaluationTask": {
                    "format": "message-single-selection",
                    "data": {
                        "messageId": some_child_ids[0]["id"],
                        "parentMessageId": some_parent_id,
                        "modelConfigName": some_child_ids[0][
                            "model_config_name"
                        ],
                    },
                }
            }
        )
        del selection["tool"]
        res.append(selection)

    return res


@pytest.fixture
def message_multi_selection_inference(
    prediction_id_mapping, mmc_example_data_row_message_ids
):
    some_parent_id, some_child_ids = next(
        iter(mmc_example_data_row_message_ids.items())
    )

    res = []
    for feature in prediction_id_mapping:
        if "message-multi-selection" not in feature:
            continue
        selection = feature["message-multi-selection"].copy()
        selection.update(
            {
                "messageEvaluationTask": {
                    "format": "message-multi-selection",
                    "data": {
                        "parentMessageId": some_parent_id,
                        "selectedMessages": [
                            {
                                "messageId": child_id["id"],
                                "modelConfigName": child_id[
                                    "model_config_name"
                                ],
                            }
                            for child_id in some_child_ids
                        ],
                    },
                }
            }
        )
        del selection["tool"]
        res.append(selection)

    return res


@pytest.fixture
def message_ranking_inference(
    prediction_id_mapping, mmc_example_data_row_message_ids
):
    some_parent_id, some_child_ids = next(
        iter(mmc_example_data_row_message_ids.items())
    )

    res = []
    for feature in prediction_id_mapping:
        if "message-ranking" not in feature:
            continue
        selection = feature["message-ranking"].copy()
        selection.update(
            {
                "messageEvaluationTask": {
                    "format": "message-ranking",
                    "data": {
                        "parentMessageId": some_parent_id,
                        "rankedMessages": [
                            {
                                "messageId": child_id["id"],
                                "modelConfigName": child_id[
                                    "model_config_name"
                                ],
                                "order": idx,
                            }
                            for idx, child_id in enumerate(
                                some_child_ids, start=1
                            )
                        ],
                    },
                }
            }
        )
        del selection["tool"]
        res.append(selection)

    return res


@pytest.fixture
def annotations_by_media_type(
    polygon_inference,
    rectangle_inference,
    rectangle_inference_document,
    line_inference_v2,
    line_inference,
    entity_inference,
    entity_inference_index,
    entity_inference_document,
    checklist_inference_index,
    text_inference_index,
    checklist_inference,
    text_inference,
    video_checklist_inference,
    prompt_text_inference,
    checklist_response_inference,
    radio_response_inference,
    text_response_inference,
    message_single_selection_inference,
    message_multi_selection_inference,
    message_ranking_inference,
    checklist_inference_index_mmc,
    radio_inference,
    radio_inference_index_mmc,
    text_inference_index_mmc,
):
    return {
        MediaType.Audio: [checklist_inference, text_inference],
        MediaType.Conversational: [
            checklist_inference_index,
            text_inference_index,
            entity_inference_index,
        ],
        MediaType.Dicom: [line_inference_v2],
        MediaType.Document: [
            entity_inference_document,
            checklist_inference,
            text_inference,
            rectangle_inference_document,
        ],
        MediaType.Html: [text_inference, checklist_inference],
        MediaType.Image: [
            polygon_inference,
            rectangle_inference,
            line_inference,
            checklist_inference,
            text_inference,
        ],
        MediaType.Text: [checklist_inference, text_inference, entity_inference],
        MediaType.Video: [video_checklist_inference],
        MediaType.LLMPromptResponseCreation: [
            prompt_text_inference,
            text_response_inference,
            checklist_response_inference,
            radio_response_inference,
        ],
        MediaType.LLMPromptCreation: [prompt_text_inference],
        OntologyKind.ResponseCreation: [
            text_response_inference,
            checklist_response_inference,
            radio_response_inference,
        ],
        OntologyKind.ModelEvaluation: [
            message_single_selection_inference,
            message_multi_selection_inference,
            message_ranking_inference,
            radio_inference,
            checklist_inference,
            text_inference,
            radio_inference_index_mmc,
            checklist_inference_index_mmc,
            text_inference_index_mmc,
        ],
    }


@pytest.fixture
def model_run_predictions(
    polygon_inference, rectangle_inference, line_inference
):
    # Not supporting mask since there isn't a signed url representing a seg mask to upload
    return polygon_inference + rectangle_inference + line_inference


@pytest.fixture
def object_predictions(
    polygon_inference,
    rectangle_inference,
    line_inference,
    entity_inference,
    segmentation_inference,
):
    return (
        polygon_inference
        + rectangle_inference
        + line_inference
        + entity_inference
        + segmentation_inference
    )


@pytest.fixture
def object_predictions_for_annotation_import(
    polygon_inference,
    rectangle_inference,
    line_inference,
    segmentation_inference,
):
    return (
        polygon_inference
        + rectangle_inference
        + line_inference
        + segmentation_inference
    )


@pytest.fixture
def classification_predictions(checklist_inference, text_inference):
    return checklist_inference + text_inference


@pytest.fixture
def predictions(object_predictions, classification_predictions):
    return object_predictions + classification_predictions


# Can only have confidence predictions supported by media type of project
@pytest.fixture
def predictions_with_confidence(rectangle_inference_with_confidence):
    return rectangle_inference_with_confidence


@pytest.fixture
def model(client, rand_gen, configured_project):
    ontology = configured_project.ontology()
    data = {"name": rand_gen(str), "ontology_id": ontology.uid}
    model = client.create_model(data["name"], data["ontology_id"])
    yield model
    try:
        model.delete()
    except:
        # Already was deleted by the test
        pass


@pytest.fixture
def model_run(rand_gen, model):
    name = rand_gen(str)
    model_run = model.create_model_run(name)
    yield model_run
    try:
        model_run.delete()
    except:
        # Already was deleted by the test
        pass


@pytest.fixture
def model_run_with_training_metadata(rand_gen, model):
    name = rand_gen(str)
    training_metadata = {"batch_size": 1000}
    model_run = model.create_model_run(name, training_metadata)
    yield model_run
    try:
        model_run.delete()
    except:
        # Already was deleted by the test
        pass


@pytest.fixture
def model_run_with_data_rows(
    client,
    configured_project,
    model_run_predictions,
    model_run,
    wait_for_label_processing,
):
    use_data_row_ids = [p["dataRow"]["id"] for p in model_run_predictions]
    model_run.upsert_data_rows(use_data_row_ids)

    upload_task = LabelImport.create_from_objects(
        client,
        configured_project.uid,
        f"label-import-{uuid.uuid4()}",
        model_run_predictions,
    )
    upload_task.wait_until_done()
    assert (
        upload_task.state == AnnotationImportState.FINISHED
    ), "Label Import did not finish"
    assert (
        len(upload_task.errors) == 0
    ), f"Label Import {upload_task.name} failed with errors {upload_task.errors}"
    labels = wait_for_label_processing(configured_project)
    label_ids = [label.uid for label in labels]
    model_run.upsert_labels(label_ids)
    yield model_run
    model_run.delete()


@pytest.fixture
def model_run_with_all_project_labels(
    client,
    configured_project,
    model_run_predictions,
    model_run: ModelRun,
    wait_for_label_processing,
):
    use_data_row_ids = list(
        set([p["dataRow"]["id"] for p in model_run_predictions])
    )

    model_run.upsert_data_rows(use_data_row_ids)

    upload_task = LabelImport.create_from_objects(
        client,
        configured_project.uid,
        f"label-import-{uuid.uuid4()}",
        model_run_predictions,
    )
    upload_task.wait_until_done()
    assert (
        upload_task.state == AnnotationImportState.FINISHED
    ), "Label Import did not finish"
    assert (
        len(upload_task.errors) == 0
    ), f"Label Import {upload_task.name} failed with errors {upload_task.errors}"
    labels = wait_for_label_processing(configured_project)
    label_ids = [label.uid for label in labels]
    model_run.upsert_labels(label_ids)
    yield model_run
    model_run.delete()


class AnnotationImportTestHelpers:
    @classmethod
    def assert_file_content(cls, url: str, predictions):
        response = requests.get(url)
        predictions = cls._convert_to_plain_object(predictions)
        assert parser.loads(response.text) == predictions

    @staticmethod
    def check_running_state(req, name, url=None):
        assert req.name == name
        if url is not None:
            assert req.input_file_url == url
        assert req.error_file_url is None
        assert req.status_file_url is None
        assert req.state == AnnotationImportState.RUNNING

    @staticmethod
    def download_and_assert_status(status_file_url):
        response = requests.get(status_file_url)
        assert response.status_code == 200
        for line in parser.loads(response.content):
            status = line["status"]
            assert status.upper() == "SUCCESS"

    @staticmethod
    def _convert_to_plain_object(obj):
        """Some Python objects e.g. tuples can't be compared with JSON serialized data, serialize to JSON and deserialize to get plain objects"""
        json_str = parser.dumps(obj)
        return parser.loads(json_str)


@pytest.fixture
def annotation_import_test_helpers() -> Type[AnnotationImportTestHelpers]:
    return AnnotationImportTestHelpers()


@pytest.fixture()
def expected_export_v2_image():
    exported_annotations = {
        "objects": [
            {
                "name": "polygon",
                "value": "polygon",
                "annotation_kind": "ImagePolygon",
                "classifications": [],
                "polygon": [
                    {"x": 147.692, "y": 118.154},
                    {"x": 142.769, "y": 104.923},
                    {"x": 57.846, "y": 118.769},
                    {"x": 28.308, "y": 169.846},
                    {"x": 147.692, "y": 118.154},
                ],
            },
            {
                "name": "bbox",
                "value": "bbox",
                "annotation_kind": "ImageBoundingBox",
                "classifications": [],
                "bounding_box": {
                    "top": 48.0,
                    "left": 58.0,
                    "height": 65.0,
                    "width": 12.0,
                },
            },
            {
                "name": "polyline",
                "value": "polyline",
                "annotation_kind": "ImagePolyline",
                "classifications": [],
                "line": [
                    {"x": 147.692, "y": 118.154},
                    {"x": 150.692, "y": 160.154},
                ],
            },
        ],
        "classifications": [
            {
                "name": "checklist",
                "value": "checklist",
                "checklist_answers": [
                    {
                        "name": "first_checklist_answer",
                        "value": "first_checklist_answer",
                        "classifications": [],
                    },
                    {
                        "name": "second_checklist_answer",
                        "value": "second_checklist_answer",
                        "classifications": [],
                    },
                ],
            },
            {
                "name": "text",
                "value": "text",
                "text_answer": {"content": "free form text..."},
            },
        ],
        "relationships": [],
    }

    return exported_annotations


@pytest.fixture()
def expected_export_v2_audio():
    expected_annotations = {
        "classifications": [
            {
                "name": "checklist",
                "value": "checklist",
                "checklist_answers": [
                    {
                        "name": "first_checklist_answer",
                        "value": "first_checklist_answer",
                        "classifications": [],
                    },
                    {
                        "name": "second_checklist_answer",
                        "value": "second_checklist_answer",
                        "classifications": [],
                    },
                ],
            },
            {
                "name": "text",
                "value": "text",
                "text_answer": {"content": "free form text..."},
            },
        ],
        "segments": {},
        "timestamp": {},
    }
    return expected_annotations


@pytest.fixture()
def expected_export_v2_html():
    expected_annotations = {
        "objects": [],
        "classifications": [
            {
                "name": "text",
                "value": "text",
                "text_answer": {"content": "free form text..."},
            },
            {
                "name": "checklist",
                "value": "checklist",
                "checklist_answers": [
                    {
                        "name": "first_checklist_answer",
                        "value": "first_checklist_answer",
                        "classifications": [],
                    },
                    {
                        "name": "second_checklist_answer",
                        "value": "second_checklist_answer",
                        "classifications": [],
                    },
                ],
            },
        ],
        "relationships": [],
    }
    return expected_annotations


@pytest.fixture()
def expected_export_v2_text():
    expected_annotations = {
        "objects": [
            {
                "name": "named-entity",
                "value": "named_entity",
                "annotation_kind": "TextEntity",
                "classifications": [],
                "location": {
                    "start": 112,
                    "end": 128,
                    "token": "research suggests",
                },
            }
        ],
        "classifications": [
            {
                "name": "checklist",
                "value": "checklist",
                "checklist_answers": [
                    {
                        "name": "first_checklist_answer",
                        "value": "first_checklist_answer",
                        "classifications": [],
                    },
                    {
                        "name": "second_checklist_answer",
                        "value": "second_checklist_answer",
                        "classifications": [],
                    },
                ],
            },
            {
                "name": "text",
                "value": "text",
                "text_answer": {"content": "free form text..."},
            },
        ],
        "relationships": [],
    }
    return expected_annotations


@pytest.fixture()
def expected_export_v2_video():
    expected_annotations = {
        "frames": {},
        "segments": {"<cuid>": [[7, 13], [18, 19]]},
        "key_frame_feature_map": {},
        "classifications": [
            {
                "name": "checklist",
                "value": "checklist",
                "checklist_answers": [
                    {
                        "name": "first_checklist_answer",
                        "value": "first_checklist_answer",
                        "classifications": [],
                    },
                    {
                        "name": "second_checklist_answer",
                        "value": "second_checklist_answer",
                        "classifications": [],
                    },
                ],
            }
        ],
    }
    return expected_annotations


@pytest.fixture()
def expected_export_v2_conversation():
    expected_annotations = {
        "objects": [
            {
                "name": "named-entity",
                "value": "named_entity",
                "annotation_kind": "ConversationalTextEntity",
                "classifications": [],
                "conversational_location": {
                    "message_id": "0",
                    "location": {"start": 0, "end": 8},
                },
            }
        ],
        "classifications": [
            {
                "name": "checklist_index",
                "value": "checklist_index",
                "message_id": "0",
                "conversational_checklist_answers": [
                    {
                        "name": "first_checklist_answer",
                        "value": "first_checklist_answer",
                        "classifications": [],
                    },
                    {
                        "name": "second_checklist_answer",
                        "value": "second_checklist_answer",
                        "classifications": [],
                    },
                ],
            },
            {
                "name": "text_index",
                "value": "text_index",
                "message_id": "0",
                "conversational_text_answer": {"content": "free form text..."},
            },
        ],
        "relationships": [],
    }
    return expected_annotations


@pytest.fixture()
def expected_export_v2_dicom():
    expected_annotations = {
        "groups": {
            "Axial": {
                "name": "Axial",
                "classifications": [],
                "frames": {
                    "1": {
                        "objects": {
                            "<cuid>": {
                                "name": "polyline",
                                "value": "polyline",
                                "annotation_kind": "DICOMPolyline",
                                "classifications": [],
                                "line": [
                                    {"x": 147.692, "y": 118.154},
                                    {"x": 150.692, "y": 160.154},
                                ],
                            }
                        },
                        "classifications": [],
                    }
                },
            },
            "Sagittal": {
                "name": "Sagittal",
                "classifications": [],
                "frames": {},
            },
            "Coronal": {"name": "Coronal", "classifications": [], "frames": {}},
        },
        "segments": {
            "Axial": {"<cuid>": [[1, 1]]},
            "Sagittal": {},
            "Coronal": {},
        },
        "classifications": [],
        "key_frame_feature_map": {
            "<cuid>": {"Axial": {"1": True}, "Coronal": {}, "Sagittal": {}}
        },
    }
    return expected_annotations


@pytest.fixture()
def expected_export_v2_document():
    expected_annotations = {
        "objects": [
            {
                "name": "named-entity",
                "value": "named_entity",
                "annotation_kind": "DocumentEntityToken",
                "classifications": [],
                "location": {
                    "groups": [
                        {
                            "id": "2f4336f4-a07e-4e0a-a9e1-5629b03b719b",
                            "page_number": 1,
                            "tokens": [
                                "3f984bf3-1d61-44f5-b59a-9658a2e3440f",
                                "3bf00b56-ff12-4e52-8cc1-08dbddb3c3b8",
                                "6e1c3420-d4b7-4c5a-8fd6-ead43bf73d80",
                                "87a43d32-af76-4a1d-b262-5c5f4d5ace3a",
                                "e8606e8a-dfd9-4c49-a635-ad5c879c75d0",
                                "67c7c19e-4654-425d-bf17-2adb8cf02c30",
                                "149c5e80-3e07-49a7-ab2d-29ddfe6a38fa",
                                "b0e94071-2187-461e-8e76-96c58738a52c",
                            ],
                            "text": "Metal-insulator (MI) transitions have been one of the",
                        }
                    ]
                },
            },
            {
                "name": "bbox",
                "value": "bbox",
                "annotation_kind": "DocumentBoundingBox",
                "classifications": [],
                "page_number": 1,
                "bounding_box": {
                    "top": 48.0,
                    "left": 58.0,
                    "height": 65.0,
                    "width": 12.0,
                },
            },
        ],
        "classifications": [
            {
                "name": "checklist",
                "value": "checklist",
                "checklist_answers": [
                    {
                        "name": "first_checklist_answer",
                        "value": "first_checklist_answer",
                        "classifications": [],
                    },
                    {
                        "name": "second_checklist_answer",
                        "value": "second_checklist_answer",
                        "classifications": [],
                    },
                ],
            },
            {
                "name": "text",
                "value": "text",
                "text_answer": {"content": "free form text..."},
            },
        ],
        "relationships": [],
    }
    return expected_annotations


@pytest.fixture()
def expected_export_v2_llm_prompt_response_creation():
    expected_annotations = {
        "objects": [],
        "classifications": [
            {
                "name": "prompt-text",
                "value": "prompt-text",
                "text_answer": {"content": "free form text..."},
            },
            {
                "name": "response-text",
                "text_answer": {"content": "free form text..."},
                "value": "response-text",
            },
            {
                "checklist_answers": [
                    {
                        "classifications": [],
                        "name": "first_checklist_answer",
                        "value": "first_checklist_answer",
                    },
                    {
                        "classifications": [],
                        "name": "second_checklist_answer",
                        "value": "second_checklist_answer",
                    },
                ],
                "name": "checklist-response",
                "value": "checklist-response",
            },
            {
                "name": "radio-response",
                "radio_answer": {
                    "classifications": [],
                    "name": "first_radio_answer",
                    "value": "first_radio_answer",
                },
                "name": "radio-response",
                "value": "radio-response",
            },
        ],
        "relationships": [],
    }
    return expected_annotations


@pytest.fixture()
def expected_export_v2_llm_prompt_creation():
    expected_annotations = {
        "objects": [],
        "classifications": [
            {
                "name": "prompt-text",
                "value": "prompt-text",
                "text_answer": {"content": "free form text..."},
            },
        ],
        "relationships": [],
    }
    return expected_annotations


@pytest.fixture()
def expected_export_v2_llm_response_creation():
    expected_annotations = {
        "objects": [],
        "relationships": [],
        "classifications": [
            {
                "name": "response-text",
                "text_answer": {"content": "free form text..."},
                "value": "response-text",
            },
            {
                "checklist_answers": [
                    {
                        "classifications": [],
                        "name": "first_checklist_answer",
                        "value": "first_checklist_answer",
                    },
                    {
                        "classifications": [],
                        "name": "second_checklist_answer",
                        "value": "second_checklist_answer",
                    },
                ],
                "name": "checklist-response",
                "value": "checklist-response",
            },
            {
                "name": "radio-response",
                "radio_answer": {
                    "classifications": [],
                    "name": "first_radio_answer",
                    "value": "first_radio_answer",
                },
                "name": "radio-response",
                "value": "radio-response",
            },
        ],
    }
    return expected_annotations


@pytest.fixture
def expected_exports_v2_mmc(mmc_example_data_row_message_ids):
    some_parent_id, some_child_ids = next(
        iter(mmc_example_data_row_message_ids.items())
    )

    return {
        "objects": [
            {
                "name": "message-single-selection",
                "annotation_kind": "MessageSingleSelection",
                "classifications": [],
                "selected_message": {
                    "message_id": some_child_ids[0]["id"],
                    "model_config_name": some_child_ids[0]["model_config_name"],
                    "parent_message_id": some_parent_id,
                },
            },
            {
                "name": "message-multi-selection",
                "annotation_kind": "MessageMultiSelection",
                "classifications": [],
                "selected_messages": {
                    "messages": [
                        {
                            "message_id": child_id["id"],
                            "model_config_name": child_id["model_config_name"],
                        }
                        for child_id in some_child_ids
                    ],
                    "parent_message_id": some_parent_id,
                },
            },
            {
                "name": "message-ranking",
                "annotation_kind": "MessageRanking",
                "classifications": [],
                "ranked_messages": {
                    "ranked_messages": [
                        {
                            "message_id": child_id["id"],
                            "model_config_name": child_id["model_config_name"],
                            "order": idx,
                        }
                        for idx, child_id in enumerate(some_child_ids, start=1)
                    ],
                    "parent_message_id": some_parent_id,
                },
            },
        ],
        "classifications": [
            {
                "name": "radio",
                "value": "radio",
                "radio_answer": {
                    "name": "first_radio_answer",
                    "value": "first_radio_answer",
                    "classifications": [],
                },
            },
            {
                "name": "checklist",
                "value": "checklist",
                "checklist_answers": [
                    {
                        "name": "first_checklist_answer",
                        "value": "first_checklist_answer",
                        "classifications": [],
                    },
                    {
                        "name": "second_checklist_answer",
                        "value": "second_checklist_answer",
                        "classifications": [],
                    },
                ],
            },
            {
                "name": "text",
                "value": "text",
                "text_answer": {"content": "free form text..."},
            },
            {
                "name": "radio_index",
                "value": "radio_index",
                "message_id": some_parent_id,
                "conversational_radio_answer": {
                    "name": "first_radio_answer",
                    "value": "first_radio_answer",
                    "classifications": [],
                },
            },
            {
                "name": "checklist_index",
                "value": "checklist_index",
                "message_id": some_parent_id,
                "conversational_checklist_answers": [
                    {
                        "name": "first_checklist_answer",
                        "value": "first_checklist_answer",
                        "classifications": [],
                    },
                    {
                        "name": "second_checklist_answer",
                        "value": "second_checklist_answer",
                        "classifications": [],
                    },
                ],
            },
            {
                "name": "text_index",
                "value": "text_index",
                "message_id": some_parent_id,
                "conversational_text_answer": {"content": "free form text..."},
            },
        ],
        "relationships": [],
    }


@pytest.fixture
def exports_v2_by_media_type(
    expected_export_v2_image,
    expected_export_v2_audio,
    expected_export_v2_html,
    expected_export_v2_text,
    expected_export_v2_video,
    expected_export_v2_conversation,
    expected_export_v2_dicom,
    expected_export_v2_document,
    expected_export_v2_llm_prompt_response_creation,
    expected_export_v2_llm_prompt_creation,
    expected_export_v2_llm_response_creation,
    expected_exports_v2_mmc,
):
    return {
        MediaType.Image: expected_export_v2_image,
        MediaType.Audio: expected_export_v2_audio,
        MediaType.Html: expected_export_v2_html,
        MediaType.Text: expected_export_v2_text,
        MediaType.Video: expected_export_v2_video,
        MediaType.Conversational: expected_export_v2_conversation,
        MediaType.Dicom: expected_export_v2_dicom,
        MediaType.Document: expected_export_v2_document,
        MediaType.LLMPromptResponseCreation: expected_export_v2_llm_prompt_response_creation,
        MediaType.LLMPromptCreation: expected_export_v2_llm_prompt_creation,
        OntologyKind.ResponseCreation: expected_export_v2_llm_response_creation,
        OntologyKind.ModelEvaluation: expected_exports_v2_mmc,
    }


class Helpers:
    @staticmethod
    def remove_keys_recursive(d, keys):
        for k in keys:
            if k in d:
                del d[k]
        for k, v in d.items():
            if isinstance(v, dict):
                Helpers.remove_keys_recursive(v, keys)
            elif isinstance(v, list):
                for i in v:
                    if isinstance(i, dict):
                        Helpers.remove_keys_recursive(i, keys)

    @staticmethod
    # NOTE this uses quite a primitive check for cuids but I do not think it is worth coming up with a better one
    # Also this function is NOT written with performance in mind, good for small to mid size dicts like we have in our test
    def rename_cuid_key_recursive(d):
        new_key = "<cuid>"
        for k in list(d.keys()):
            if len(k) == 25 and not k.isalpha():  # primitive check for cuid
                d[new_key] = d.pop(k)
        for k, v in d.items():
            if isinstance(v, dict):
                Helpers.rename_cuid_key_recursive(v)
            elif isinstance(v, list):
                for i in v:
                    if isinstance(i, dict):
                        Helpers.rename_cuid_key_recursive(i)

    @staticmethod
    def set_project_media_type_from_data_type(project, data_type_class):
        def to_pascal_case(name: str) -> str:
            return "".join([word.capitalize() for word in name.split("_")])

        data_type_string = data_type_class.__name__[:-4].lower()
        media_type = to_pascal_case(data_type_string)
        if media_type == "Conversational":
            media_type = "Conversational"
        elif media_type == "Llmpromptcreation":
            media_type = "LLMPromptCreation"
        elif media_type == "Llmpromptresponsecreation":
            media_type = "LLMPromptResponseCreation"
        elif media_type == "Llmresponsecreation":
            media_type = "Text"
        elif media_type == "Genericdatarow":
            media_type = "Image"
        project.update(media_type=MediaType[media_type])

    @staticmethod
    def find_data_row_filter(data_row):
        return lambda dr: dr["data_row"]["id"] == data_row.uid


@pytest.fixture
def helpers():
    return Helpers
