import uuid

import pytest
import time
import requests

from labelbox import parser, MediaType

from typing import Type
from labelbox.schema.labeling_frontend import LabelingFrontend
from labelbox.schema.annotation_import import LabelImport, AnnotationImportState
from labelbox.schema.project import Project
from labelbox.schema.queue_mode import QueueMode

DATA_ROW_PROCESSING_WAIT_TIMEOUT_SECONDS = 40
DATA_ROW_PROCESSING_WAIT_SLEEP_INTERNAL_SECONDS = 7


@pytest.fixture()
def audio_data_row(rand_gen):
    return {
        "row_data":
            "https://storage.googleapis.com/labelbox-datasets/audio-sample-data/sample-audio-1.mp3",
        "global_key":
            f"https://storage.googleapis.com/labelbox-datasets/audio-sample-data/sample-audio-1.mp3-{rand_gen(str)}",
        "media_type":
            "AUDIO",
    }


@pytest.fixture()
def conversation_data_row(rand_gen):
    return {
        "row_data":
            "https://storage.googleapis.com/labelbox-developer-testing-assets/conversational_text/1000-conversations/conversation-1.json",
        "global_key":
            f"https://storage.googleapis.com/labelbox-developer-testing-assets/conversational_text/1000-conversations/conversation-1.json-{rand_gen(str)}",
    }


@pytest.fixture()
def dicom_data_row(rand_gen):
    return {
        "row_data":
            "https://storage.googleapis.com/labelbox-datasets/dicom-sample-data/sample-dicom-1.dcm",
        "global_key":
            f"https://storage.googleapis.com/labelbox-datasets/dicom-sample-data/sample-dicom-1.dcm-{rand_gen(str)}",
        "media_type":
            "DICOM",
    }


@pytest.fixture()
def geospatial_data_row(rand_gen):
    return {
        "row_data": {
            "tile_layer_url":
                "https://s3-us-west-1.amazonaws.com/lb-tiler-layers/mexico_city/{z}/{x}/{y}.png",
            "bounds": [[19.405662413477728, -99.21052827588443],
                       [19.400498983095076, -99.20534818927473]],
            "min_zoom":
                12,
            "max_zoom":
                20,
            "epsg":
                "EPSG4326",
        },
        "global_key":
            f"https://s3-us-west-1.amazonaws.com/lb-tiler-layers/mexico_city/z/x/y.png-{rand_gen(str)}",
        "media_type":
            "TMS_GEO",
    }


@pytest.fixture()
def html_data_row(rand_gen):
    return {
        "row_data":
            "https://storage.googleapis.com/labelbox-datasets/html_sample_data/sample_html_1.html",
        "global_key":
            f"https://storage.googleapis.com/labelbox-datasets/html_sample_data/sample_html_1.html-{rand_gen(str)}",
    }


@pytest.fixture()
def image_data_row(rand_gen):
    return {
        "row_data":
            "https://lb-test-data.s3.us-west-1.amazonaws.com/image-samples/sample-image-1.jpg",
        "global_key":
            f"https://lb-test-data.s3.us-west-1.amazonaws.com/image-samples/sample-image-1.jpg-{rand_gen(str)}",
        "media_type":
            "IMAGE",
    }


@pytest.fixture()
def document_data_row(rand_gen):
    return {
        "row_data": {
            "pdf_url":
                "https://storage.googleapis.com/labelbox-datasets/arxiv-pdf/data/99-word-token-pdfs/0801.3483.pdf",
            "text_layer_url":
                "https://storage.googleapis.com/labelbox-datasets/arxiv-pdf/data/99-word-token-pdfs/0801.3483-lb-textlayer.json"
        },
        "global_key":
            f"https://storage.googleapis.com/labelbox-datasets/arxiv-pdf/data/99-word-token-pdfs/0801.3483.pdf-{rand_gen(str)}",
        "media_type":
            "PDF",
    }


@pytest.fixture()
def text_data_row(rand_gen):
    return {
        "row_data":
            "https://storage.googleapis.com/lb-artifacts-testing-public/sdk_integration_test/sample-text-1.txt",
        "global_key":
            f"https://storage.googleapis.com/lb-artifacts-testing-public/sdk_integration_test/sample-text-1.txt-{rand_gen(str)}",
        "media_type":
            "TEXT",
    }


@pytest.fixture()
def llm_prompt_creation_data_row(rand_gen):
    return {
        "row_data": {
            "type": "application/llm.prompt-creation",
            "version": 1
        },
        "global_key": rand_gen(str)
    }


@pytest.fixture()
def llm_prompt_response_data_row(rand_gen):
    return {
        "row_data": {
            "type": "application/llm.prompt-response-creation",
            "version": 1
        },
        "global_key": rand_gen(str)
    }


@pytest.fixture
def data_row_json_by_data_type(audio_data_row, conversation_data_row,
                               dicom_data_row, geospatial_data_row,
                               html_data_row, image_data_row, document_data_row,
                               text_data_row, video_data_row,
                               llm_prompt_creation_data_row,
                               llm_prompt_response_data_row):
    return {
        'audio': audio_data_row,
        'conversation': conversation_data_row,
        'dicom': dicom_data_row,
        'geospatial': geospatial_data_row,
        'html': html_data_row,
        'image': image_data_row,
        'document': document_data_row,
        'text': text_data_row,
        'video': video_data_row,
        'llmpromptcreation': llm_prompt_creation_data_row,
        'llmpromptresponsecreation': llm_prompt_response_data_row,
        'llmresponsecreation': text_data_row
    }


@pytest.fixture
def exports_v2_by_data_type(expected_export_v2_image, expected_export_v2_audio,
                            expected_export_v2_html, expected_export_v2_text,
                            expected_export_v2_video,
                            expected_export_v2_conversation,
                            expected_export_v2_dicom,
                            expected_export_v2_document,
                            expected_export_v2_llm_prompt_creation,
                            expected_export_v2_llm_prompt_response_creation,
                            expected_export_v2_llm_response_creation):
    return {
        'image':
            expected_export_v2_image,
        'audio':
            expected_export_v2_audio,
        'html':
            expected_export_v2_html,
        'text':
            expected_export_v2_text,
        'video':
            expected_export_v2_video,
        'conversation':
            expected_export_v2_conversation,
        'dicom':
            expected_export_v2_dicom,
        'document':
            expected_export_v2_document,
        'llmpromptcreation':
            expected_export_v2_llm_prompt_creation,
        'llmpromptresponsecreation':
            expected_export_v2_llm_prompt_response_creation,
        'llmresponsecreation':
            expected_export_v2_llm_response_creation
    }


@pytest.fixture
def annotations_by_data_type(polygon_inference, rectangle_inference,
                             rectangle_inference_document, line_inference,
                             entity_inference, entity_inference_document,
                             checklist_inference, text_inference,
                             video_checklist_inference):
    return {
        'audio': [checklist_inference, text_inference],
        'conversation': [checklist_inference, text_inference, entity_inference],
        'dicom': [line_inference],
        'document': [
            entity_inference_document, checklist_inference, text_inference,
            rectangle_inference_document
        ],
        'html': [text_inference, checklist_inference],
        'image': [
            polygon_inference, rectangle_inference, line_inference,
            checklist_inference, text_inference
        ],
        'text': [entity_inference, checklist_inference, text_inference],
        'video': [video_checklist_inference],
        'llmpromptcreation': [checklist_inference, text_inference],
        'llmpromptresponsecreation': [checklist_inference, text_inference],
        'llmresponsecreation': [checklist_inference, text_inference]
    }


@pytest.fixture
def annotations_by_data_type_v2(
        polygon_inference, rectangle_inference, rectangle_inference_document,
        line_inference_v2, line_inference, entity_inference,
        entity_inference_index, entity_inference_document,
        checklist_inference_index, text_inference_index, checklist_inference,
        text_inference, video_checklist_inference):
    return {
        'audio': [checklist_inference, text_inference],
        'conversation': [
            checklist_inference_index, text_inference_index,
            entity_inference_index
        ],
        'dicom': [line_inference_v2],
        'document': [
            entity_inference_document, checklist_inference, text_inference,
            rectangle_inference_document
        ],
        'html': [text_inference, checklist_inference],
        'image': [
            polygon_inference, rectangle_inference, line_inference,
            checklist_inference, text_inference
        ],
        'text': [entity_inference, checklist_inference, text_inference],
        'video': [video_checklist_inference],
        'llmpromptcreation': [checklist_inference, text_inference],
        'llmpromptresponsecreation': [checklist_inference, text_inference],
        'llmresponsecreation': [checklist_inference, text_inference]
    }


@pytest.fixture(scope='session')
def ontology():
    bbox_tool_with_nested_text = {
        'required':
            False,
        'name':
            'bbox_tool_with_nested_text',
        'tool':
            'rectangle',
        'color':
            '#a23030',
        'classifications': [{
            'required':
                False,
            'instructions':
                'nested',
            'name':
                'nested',
            'type':
                'radio',
            'options': [{
                'label':
                    'radio_option_1',
                'value':
                    'radio_value_1',
                'options': [{
                    'required':
                        False,
                    'instructions':
                        'nested_checkbox',
                    'name':
                        'nested_checkbox',
                    'type':
                        'checklist',
                    'options': [{
                        'label': 'nested_checkbox_option_1',
                        'value': 'nested_checkbox_value_1',
                        'options': []
                    }, {
                        'label': 'nested_checkbox_option_2',
                        'value': 'nested_checkbox_value_2'
                    }]
                }, {
                    'required': False,
                    'instructions': 'nested_text',
                    'name': 'nested_text',
                    'type': 'text',
                    'options': []
                }]
            },]
        }]
    }

    bbox_tool = {
        'required':
            False,
        'name':
            'bbox',
        'tool':
            'rectangle',
        'color':
            '#a23030',
        'classifications': [{
            'required':
                False,
            'instructions':
                'nested',
            'name':
                'nested',
            'type':
                'radio',
            'options': [{
                'label':
                    'radio_option_1',
                'value':
                    'radio_value_1',
                'options': [{
                    'required':
                        False,
                    'instructions':
                        'nested_checkbox',
                    'name':
                        'nested_checkbox',
                    'type':
                        'checklist',
                    'options': [{
                        'label': 'nested_checkbox_option_1',
                        'value': 'nested_checkbox_value_1',
                        'options': []
                    }, {
                        'label': 'nested_checkbox_option_2',
                        'value': 'nested_checkbox_value_2'
                    }]
                }]
            },]
        }]
    }

    polygon_tool = {
        'required': False,
        'name': 'polygon',
        'tool': 'polygon',
        'color': '#FF34FF',
        'classifications': []
    }
    polyline_tool = {
        'required': False,
        'name': 'polyline',
        'tool': 'line',
        'color': '#FF4A46',
        'classifications': []
    }
    point_tool = {
        'required': False,
        'name': 'point--',
        'tool': 'point',
        'color': '#008941',
        'classifications': []
    }
    entity_tool = {
        'required': False,
        'name': 'entity--',
        'tool': 'named-entity',
        'color': '#006FA6',
        'classifications': []
    }
    segmentation_tool = {
        'required': False,
        'name': 'segmentation--',
        'tool': 'superpixel',
        'color': '#A30059',
        'classifications': []
    }
    raster_segmentation_tool = {
        'required': False,
        'name': 'segmentation_mask',
        'tool': 'raster-segmentation',
        'color': '#ff0000',
        'classifications': []
    }
    checklist = {
        'required':
            False,
        'instructions':
            'checklist',
        'name':
            'checklist',
        'type':
            'checklist',
        'options': [{
            'label': 'option1',
            'value': 'option1'
        }, {
            'label': 'option2',
            'value': 'option2'
        }, {
            'label': 'optionN',
            'value': 'optionn'
        }]
    }
    checklist_index = {
        'required':
            False,
        'instructions':
            'checklist_index',
        'name':
            'checklist_index',
        'type':
            'checklist',
        'scope':
            'index',
        'options': [{
            'label': 'option1_index',
            'value': 'option1_index'
        }, {
            'label': 'option2_index',
            'value': 'option2_index'
        }, {
            'label': 'optionN_index',
            'value': 'optionn_index'
        }]
    }
    free_form_text = {
        'required': False,
        'instructions': 'text',
        'name': 'text',
        'type': 'text',
        'options': []
    }
    free_form_text_index = {
        'required': False,
        'instructions': 'text_index',
        'name': 'text_index',
        'type': 'text',
        'scope': 'index',
        'options': []
    }
    radio = {
        'required':
            False,
        'instructions':
            'radio',
        'name':
            'radio',
        'type':
            'radio',
        'options': [{
            'label': 'first_radio_answer',
            'value': 'first_radio_answer',
            'options': []
        }, {
            'label': 'second_radio_answer',
            'value': 'second_radio_answer',
            'options': []
        }]
    }
    named_entity = {
        'tool': 'named-entity',
        'name': 'named-entity',
        'required': False,
        'color': '#A30059',
        'classifications': [],
    }

    tools = [
        bbox_tool,
        bbox_tool_with_nested_text,
        polygon_tool,
        polyline_tool,
        point_tool,
        entity_tool,
        segmentation_tool,
        raster_segmentation_tool,
        named_entity,
    ]
    classifications = [
        checklist, checklist_index, free_form_text, free_form_text_index, radio
    ]
    return {"tools": tools, "classifications": classifications}


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


@pytest.fixture
def configured_project_datarow_id(configured_project):

    def get_data_row_id(indx=0):
        return configured_project.data_row_ids[indx]

    yield get_data_row_id


@pytest.fixture
def configured_project_one_datarow_id(configured_project_with_one_data_row):

    def get_data_row_id(indx=0):
        return configured_project_with_one_data_row.data_row_ids[0]

    yield get_data_row_id


@pytest.fixture
def configured_project(client, initial_dataset, ontology, rand_gen, image_url):
    dataset = initial_dataset
    project = client.create_project(name=rand_gen(str),
                                    queue_mode=QueueMode.Batch)
    editor = list(
        client.get_labeling_frontends(
            where=LabelingFrontend.name == "editor"))[0]
    project.setup(editor, ontology)

    data_row_ids = []

    ontologies = ontology['tools'] + ontology['classifications']
    for ind in range(len(ontologies)):
        data_row_ids.append(
            dataset.create_data_row(
                row_data=image_url,
                global_key=f"gk_{ontologies[ind]['name']}_{rand_gen(str)}").uid)
    project._wait_until_data_rows_are_processed(data_row_ids=data_row_ids,
                                                sleep_interval=3)

    project.create_batch(
        rand_gen(str),
        data_row_ids,  # sample of data row objects
        5  # priority between 1(Highest) - 5(lowest)
    )
    project.data_row_ids = data_row_ids

    yield project

    project.delete()


@pytest.fixture
def project_with_ontology(client, configured_project, ontology, rand_gen):
    project = client.create_project(name=rand_gen(str),
                                    queue_mode=QueueMode.Batch,
                                    media_type=MediaType.Image)
    editor = list(
        client.get_labeling_frontends(
            where=LabelingFrontend.name == "editor"))[0]
    project.setup(editor, ontology)

    yield project, ontology

    project.delete()


@pytest.fixture
def configured_project_pdf(client, ontology, rand_gen, pdf_url):
    project = client.create_project(name=rand_gen(str),
                                    queue_mode=QueueMode.Batch,
                                    media_type=MediaType.Pdf)
    dataset = client.create_dataset(name=rand_gen(str))
    editor = list(
        client.get_labeling_frontends(
            where=LabelingFrontend.name == "editor"))[0]
    project.setup(editor, ontology)
    data_row = dataset.create_data_row(pdf_url)
    data_row_ids = [data_row.uid]
    project.create_batch(
        rand_gen(str),
        data_row_ids,  # sample of data row objects
        5  # priority between 1(Highest) - 5(lowest)
    )
    project.data_row_ids = data_row_ids
    yield project
    project.delete()
    dataset.delete()


@pytest.fixture
def dataset_pdf_entity(client, rand_gen, document_data_row):
    dataset = client.create_dataset(name=rand_gen(str))
    data_row_ids = []
    data_row = dataset.create_data_row(document_data_row)
    data_row_ids.append(data_row.uid)
    yield dataset, data_row_ids
    dataset.delete()


@pytest.fixture
def dataset_conversation_entity(client, rand_gen, conversation_entity_data_row,
                                wait_for_data_row_processing):
    dataset = client.create_dataset(name=rand_gen(str))
    data_row_ids = []
    data_row = dataset.create_data_row(conversation_entity_data_row)
    data_row = wait_for_data_row_processing(client, data_row)

    data_row_ids.append(data_row.uid)
    yield dataset, data_row_ids
    dataset.delete()


@pytest.fixture
def configured_project_with_one_data_row(client, ontology, rand_gen,
                                         initial_dataset, image_url):
    project = client.create_project(name=rand_gen(str),
                                    description=rand_gen(str),
                                    queue_mode=QueueMode.Batch)
    editor = list(
        client.get_labeling_frontends(
            where=LabelingFrontend.name == "editor"))[0]
    project.setup(editor, ontology)

    data_row = initial_dataset.create_data_row(row_data=image_url)
    data_row_ids = [data_row.uid]
    project._wait_until_data_rows_are_processed(data_row_ids=data_row_ids,
                                                sleep_interval=3)

    batch = project.create_batch(
        rand_gen(str),
        data_row_ids,  # sample of data row objects
        5  # priority between 1(Highest) - 5(lowest)
    )
    project.data_row_ids = data_row_ids

    yield project

    batch.delete()
    project.delete()


# This function allows to convert an ontology feature to actual annotation
# At the moment it expects only one feature per tool type and this creates unnecessary coupling between differet tests
# In an example of a 'rectangle' we have extended to support multiple instances of the same tool type
# TODO: we will support this approach in the future for all tools
#
"""
Please note that this fixture now offers the flexibility to configure three different strategies for generating data row ids for predictions:
Default(configured_project fixture):
    configured_project that generates a data row for each member of ontology.
    This makes sure each prediction has its own data row id. This is applicable to prediction upload cases when last label overwrites existing ones

Optimized Strategy (configured_project_with_one_data_row fixture):
    This fixture has only one data row and all predictions will be mapped to it

Custom Data Row IDs Strategy:
    Individuals can supply hard-coded data row ids when a creation of data row is not required. 
    This particular fixture, termed "hardcoded_datarow_id," should be defined locally within a test file.
    In the future, we can use this approach to inject correct number of rows instead of using configured_project fixture 
        that creates a data row for each member of ontology (14 in total) for each run.
"""


@pytest.fixture
def prediction_id_mapping(ontology, request):
    # Maps tool types to feature schema ids
    if 'configured_project' in request.fixturenames:
        data_row_id_factory = request.getfixturevalue(
            'configured_project_datarow_id')
        project = request.getfixturevalue('configured_project')
    elif 'hardcoded_datarow_id' in request.fixturenames:
        data_row_id_factory = request.getfixturevalue('hardcoded_datarow_id')
        project = request.getfixturevalue('configured_project_with_ontology')
    else:
        data_row_id_factory = request.getfixturevalue(
            'configured_project_one_datarow_id')
        project = request.getfixturevalue(
            'configured_project_with_one_data_row')

    ontology = project.ontology().normalized

    result = {}

    for idx, tool in enumerate(ontology['tools'] + ontology['classifications']):
        if 'tool' in tool:
            tool_type = tool['tool']
        else:
            tool_type = tool[
                'type'] if 'scope' not in tool else f"{tool['type']}_{tool['scope']}"  # so 'checklist' of 'checklist_index'

        # TODO: remove this once we have a better way to associate multiple tools instances with a single tool type
        if tool_type == 'rectangle':
            value = {
                "uuid": str(uuid.uuid4()),
                "schemaId": tool['featureSchemaId'],
                "name": tool['name'],
                "dataRow": {
                    "id": data_row_id_factory(idx),
                },
                'tool': tool
            }
            if tool_type not in result:
                result[tool_type] = []
            result[tool_type].append(value)
        else:
            result[tool_type] = {
                "uuid": str(uuid.uuid4()),
                "schemaId": tool['featureSchemaId'],
                "name": tool['name'],
                "dataRow": {
                    "id": data_row_id_factory(idx),
                },
                'tool': tool
            }
    return result


@pytest.fixture
def polygon_inference(prediction_id_mapping):
    polygon = prediction_id_mapping['polygon'].copy()
    polygon.update({
        "polygon": [{
            "x": 147.692,
            "y": 118.154
        }, {
            "x": 142.769,
            "y": 104.923
        }, {
            "x": 57.846,
            "y": 118.769
        }, {
            "x": 28.308,
            "y": 169.846
        }]
    })
    del polygon['tool']
    return polygon


def find_tool_by_name(tool_instances, name):
    for tool in tool_instances:
        if tool['name'] == name:
            return tool
    return None


@pytest.fixture
def rectangle_inference(prediction_id_mapping):
    tool_instance = find_tool_by_name(prediction_id_mapping['rectangle'],
                                      'bbox')
    rectangle = tool_instance.copy()
    rectangle.update({
        "bbox": {
            "top": 48,
            "left": 58,
            "height": 65,
            "width": 12
        },
        'classifications': [{
            "schemaId":
                rectangle['tool']['classifications'][0]['featureSchemaId'],
            "name":
                rectangle['tool']['classifications'][0]['name'],
            "answer": {
                "schemaId":
                    rectangle['tool']['classifications'][0]['options'][0]
                    ['featureSchemaId'],
                "name":
                    rectangle['tool']['classifications'][0]['options'][0]
                    ['value']
            }
        }]
    })
    del rectangle['tool']
    return rectangle


@pytest.fixture
def rectangle_inference_with_confidence(prediction_id_mapping):
    tool_instance = find_tool_by_name(prediction_id_mapping['rectangle'],
                                      'bbox_tool_with_nested_text')
    rectangle = tool_instance.copy()
    rectangle.update({
        "bbox": {
            "top": 48,
            "left": 58,
            "height": 65,
            "width": 12
        },
        'classifications': [{
            "schemaId":
                rectangle['tool']['classifications'][0]['featureSchemaId'],
            "name":
                rectangle['tool']['classifications'][0]['name'],
            "answer": {
                "schemaId":
                    rectangle['tool']['classifications'][0]['options'][0]
                    ['featureSchemaId'],
                "name":
                    rectangle['tool']['classifications'][0]['options'][0]
                    ['value'],
                "classifications": [{
                    "schemaId":
                        rectangle['tool']['classifications'][0]['options'][0]
                        ['options'][1]['featureSchemaId'],
                    "name":
                        rectangle['tool']['classifications'][0]['options'][0]
                        ['options'][1]['name'],
                    "answer":
                        'nested answer'
                }],
            }
        }]
    })

    rectangle.update({"confidence": 0.9})
    rectangle["classifications"][0]["answer"]["confidence"] = 0.8
    rectangle["classifications"][0]["answer"]["classifications"][0][
        "confidence"] = 0.7

    del rectangle['tool']
    return rectangle


@pytest.fixture
def rectangle_inference_document(rectangle_inference):
    rectangle = rectangle_inference.copy()
    rectangle.update({"page": 1, "unit": "POINTS"})
    return rectangle


@pytest.fixture
def line_inference(prediction_id_mapping):
    line = prediction_id_mapping['line'].copy()
    line.update(
        {"line": [{
            "x": 147.692,
            "y": 118.154
        }, {
            "x": 150.692,
            "y": 160.154
        }]})
    del line['tool']
    return line


@pytest.fixture
def line_inference_v2(prediction_id_mapping):
    line = prediction_id_mapping['line'].copy()
    line_data = {
        "groupKey":
            "axial",
        "segments": [{
            "keyframes": [{
                "frame":
                    1,
                "line": [{
                    "x": 147.692,
                    "y": 118.154
                }, {
                    "x": 150.692,
                    "y": 160.154
                }]
            }]
        },]
    }
    line.update(line_data)
    del line['tool']
    return line


@pytest.fixture
def point_inference(prediction_id_mapping):
    point = prediction_id_mapping['point'].copy()
    point.update({"point": {"x": 147.692, "y": 118.154}})
    del point['tool']
    return point


@pytest.fixture
def entity_inference(prediction_id_mapping):
    entity = prediction_id_mapping['named-entity'].copy()
    entity.update({"location": {"start": 67, "end": 128}})
    del entity['tool']
    return entity


@pytest.fixture
def entity_inference_index(prediction_id_mapping):
    entity = prediction_id_mapping['named-entity'].copy()
    entity.update({
        "location": {
            "start": 0,
            "end": 8
        },
        "messageId": "0",
    })

    del entity['tool']
    return entity


@pytest.fixture
def entity_inference_document(prediction_id_mapping):
    entity = prediction_id_mapping['named-entity'].copy()
    document_selections = {
        "textSelections": [{
            "tokenIds": [
                "3f984bf3-1d61-44f5-b59a-9658a2e3440f",
                "3bf00b56-ff12-4e52-8cc1-08dbddb3c3b8",
                "6e1c3420-d4b7-4c5a-8fd6-ead43bf73d80",
                "87a43d32-af76-4a1d-b262-5c5f4d5ace3a",
                "e8606e8a-dfd9-4c49-a635-ad5c879c75d0",
                "67c7c19e-4654-425d-bf17-2adb8cf02c30",
                "149c5e80-3e07-49a7-ab2d-29ddfe6a38fa",
                "b0e94071-2187-461e-8e76-96c58738a52c"
            ],
            "groupId": "2f4336f4-a07e-4e0a-a9e1-5629b03b719b",
            "page": 1,
        }]
    }
    entity.update(document_selections)
    del entity['tool']
    return entity


@pytest.fixture
def segmentation_inference(prediction_id_mapping):
    segmentation = prediction_id_mapping['superpixel'].copy()
    segmentation.update({
        'mask': {
            "instanceURI":
                "https://storage.googleapis.com/labelbox-datasets/image_sample_data/raster_seg.png",
            "colorRGB": (255, 255, 255)
        }
    })
    del segmentation['tool']
    return segmentation


@pytest.fixture
def segmentation_inference_rle(prediction_id_mapping):
    segmentation = prediction_id_mapping['superpixel'].copy()
    segmentation.update({
        'uuid': str(uuid.uuid4()),
        'mask': {
            'size': [10, 10],
            'counts': [1, 0, 10, 100]
        }
    })
    del segmentation['tool']
    return segmentation


@pytest.fixture
def segmentation_inference_png(prediction_id_mapping):
    segmentation = prediction_id_mapping['superpixel'].copy()
    segmentation.update({
        'uuid': str(uuid.uuid4()),
        'mask': {
            'png': "somedata",
        }
    })
    del segmentation['tool']
    return segmentation


@pytest.fixture
def checklist_inference(prediction_id_mapping):
    checklist = prediction_id_mapping['checklist'].copy()
    checklist.update({
        'answers': [{
            'schemaId': checklist['tool']['options'][0]['featureSchemaId']
        }]
    })
    del checklist['tool']
    return checklist


@pytest.fixture
def checklist_inference_index(prediction_id_mapping):
    checklist = prediction_id_mapping['checklist_index'].copy()
    checklist.update({
        'answers': [{
            'schemaId': checklist['tool']['options'][0]['featureSchemaId']
        }],
        "messageId": "0",
    })
    del checklist['tool']
    return checklist


@pytest.fixture
def text_inference(prediction_id_mapping):
    text = prediction_id_mapping['text'].copy()
    text.update({'answer': "free form text..."})
    del text['tool']
    return text


@pytest.fixture
def text_inference_with_confidence(text_inference):
    text = text_inference.copy()
    text.update({'confidence': 0.9})
    return text


@pytest.fixture
def text_inference_index(prediction_id_mapping):
    text = prediction_id_mapping['text_index'].copy()
    text.update({'answer': "free form text...", "messageId": "0"})
    del text['tool']
    return text


@pytest.fixture
def video_checklist_inference(prediction_id_mapping):
    checklist = prediction_id_mapping['checklist'].copy()
    checklist.update({
        'answers': [{
            'schemaId': checklist['tool']['options'][0]['featureSchemaId']
        }]
    })

    checklist.update(
        {"frames": [{
            "start": 7,
            "end": 13,
        }, {
            "start": 18,
            "end": 19,
        }]})
    del checklist['tool']
    return checklist


@pytest.fixture
def model_run_predictions(polygon_inference, rectangle_inference,
                          line_inference):
    # Not supporting mask since there isn't a signed url representing a seg mask to upload
    return [polygon_inference, rectangle_inference, line_inference]


@pytest.fixture
def object_predictions(polygon_inference, rectangle_inference, line_inference,
                       entity_inference, segmentation_inference):
    return [
        polygon_inference, rectangle_inference, line_inference,
        entity_inference, segmentation_inference
    ]


@pytest.fixture
def object_predictions_for_annotation_import(polygon_inference,
                                             rectangle_inference,
                                             line_inference,
                                             segmentation_inference):
    return [
        polygon_inference, rectangle_inference, line_inference,
        segmentation_inference
    ]


@pytest.fixture
def classification_predictions(checklist_inference, text_inference):
    return [checklist_inference, text_inference]


@pytest.fixture
def predictions(object_predictions, classification_predictions):
    return object_predictions + classification_predictions


@pytest.fixture
def predictions_with_confidence(text_inference_with_confidence,
                                rectangle_inference_with_confidence):
    return [text_inference_with_confidence, rectangle_inference_with_confidence]


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
def model_run_with_data_rows(client, configured_project, model_run_predictions,
                             model_run, wait_for_label_processing):
    configured_project.enable_model_assisted_labeling()
    use_data_row_ids = [p['dataRow']['id'] for p in model_run_predictions]
    model_run.upsert_data_rows(use_data_row_ids)

    upload_task = LabelImport.create_from_objects(
        client, configured_project.uid, f"label-import-{uuid.uuid4()}",
        model_run_predictions)
    upload_task.wait_until_done()
    assert upload_task.state == AnnotationImportState.FINISHED, "Label Import did not finish"
    assert len(
        upload_task.errors
    ) == 0, f"Label Import {upload_task.name} failed with errors {upload_task.errors}"
    labels = wait_for_label_processing(configured_project)
    label_ids = [label.uid for label in labels]
    model_run.upsert_labels(label_ids)
    yield model_run
    model_run.delete()
    # TODO: Delete resources when that is possible ..


@pytest.fixture
def model_run_with_all_project_labels(client, configured_project,
                                      model_run_predictions, model_run,
                                      wait_for_label_processing):
    configured_project.enable_model_assisted_labeling()
    use_data_row_ids = [p['dataRow']['id'] for p in model_run_predictions]
    model_run.upsert_data_rows(use_data_row_ids)

    upload_task = LabelImport.create_from_objects(
        client, configured_project.uid, f"label-import-{uuid.uuid4()}",
        model_run_predictions)
    upload_task.wait_until_done()
    assert upload_task.state == AnnotationImportState.FINISHED, "Label Import did not finish"
    assert len(
        upload_task.errors
    ) == 0, f"Label Import {upload_task.name} failed with errors {upload_task.errors}"
    wait_for_label_processing(configured_project)
    model_run.upsert_labels(project_id=configured_project.uid)
    yield model_run
    model_run.delete()
    # TODO: Delete resources when that is possible ..


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
            status = line['status']
            assert status.upper() == 'SUCCESS'

    @staticmethod
    def _convert_to_plain_object(obj):
        """Some Python objects e.g. tuples can't be compared with JSON serialized data, serialize to JSON and deserialize to get plain objects"""
        json_str = parser.dumps(obj)
        return parser.loads(json_str)


@pytest.fixture
def annotation_import_test_helpers() -> Type[AnnotationImportTestHelpers]:
    return AnnotationImportTestHelpers()
