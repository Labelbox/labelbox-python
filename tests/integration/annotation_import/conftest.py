import uuid

import pytest
import time
import requests
import ndjson

from typing import Type
from labelbox.schema.labeling_frontend import LabelingFrontend
from labelbox.schema.annotation_import import LabelImport, AnnotationImportState
from labelbox.schema.queue_mode import QueueMode


@pytest.fixture
def ontology():
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
            'required': False,
            'instructions': 'nested',
            'name': 'nested',
            'type': 'radio',
            'options': [{
                'label': 'radio_option_1',
                'value': 'radio_value_1'
            }]
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
    free_form_text = {
        'required': False,
        'instructions': 'text',
        'name': 'text',
        'type': 'text',
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
        bbox_tool, polygon_tool, polyline_tool, point_tool, entity_tool,
        segmentation_tool, named_entity
    ]
    classifications = [checklist, free_form_text, radio]
    return {"tools": tools, "classifications": classifications}


@pytest.fixture
def configured_project(client, ontology, rand_gen, image_url):
    project = client.create_project(name=rand_gen(str),
                                    queue_mode=QueueMode.Dataset)
    dataset = client.create_dataset(name=rand_gen(str))
    editor = list(
        client.get_labeling_frontends(
            where=LabelingFrontend.name == "editor"))[0]
    project.setup(editor, ontology)
    data_row_ids = []
    for _ in range(len(ontology['tools']) + len(ontology['classifications'])):
        data_row_ids.append(dataset.create_data_row(row_data=image_url).uid)
    project.datasets.connect(dataset)
    project.data_row_ids = data_row_ids
    yield project
    project.delete()
    dataset.delete()


@pytest.fixture
def configured_project_pdf(client, ontology, rand_gen, pdf_url):
    project = client.create_project(name=rand_gen(str),
                                    queue_mode=QueueMode.Dataset)
    dataset = client.create_dataset(name=rand_gen(str))
    editor = list(
        client.get_labeling_frontends(
            where=LabelingFrontend.name == "editor"))[0]
    project.setup(editor, ontology)
    data_row_ids = []
    data_row_ids.append(dataset.create_data_row(pdf_url).uid)
    project.datasets.connect(dataset)
    project.data_row_ids = data_row_ids
    yield project
    project.delete()
    dataset.delete()


@pytest.fixture
def dataset_pdf_entity(client, rand_gen, pdf_entity_data_row):
    dataset = client.create_dataset(name=rand_gen(str))
    data_row_ids = []
    data_row = dataset.create_data_row(pdf_entity_data_row)
    data_row_ids.append(data_row.uid)
    yield dataset, data_row_ids
    dataset.delete()


@pytest.fixture
def configured_project_without_data_rows(client, configured_project, rand_gen):
    project = client.create_project(name=rand_gen(str),
                                    description=rand_gen(str),
                                    queue_mode=QueueMode.Batch)
    editor = list(
        client.get_labeling_frontends(
            where=LabelingFrontend.name == "editor"))[0]
    project.setup_editor(configured_project.ontology())
    yield project
    project.delete()


@pytest.fixture
def prediction_id_mapping(configured_project):
    # Maps tool types to feature schema ids
    ontology = configured_project.ontology().normalized
    result = {}

    for idx, tool in enumerate(ontology['tools'] + ontology['classifications']):
        if 'tool' in tool:
            tool_type = tool['tool']
        else:
            tool_type = tool['type']
        result[tool_type] = {
            "uuid": str(uuid.uuid4()),
            "schemaId": tool['featureSchemaId'],
            "name": tool['name'],
            "dataRow": {
                "id": configured_project.data_row_ids[idx],
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
            "y": 404.923
        }, {
            "x": 57.846,
            "y": 318.769
        }, {
            "x": 28.308,
            "y": 169.846
        }]
    })
    del polygon['tool']
    return polygon


@pytest.fixture
def rectangle_inference(prediction_id_mapping):
    rectangle = prediction_id_mapping['rectangle'].copy()
    rectangle.update({
        "bbox": {
            "top": 48,
            "left": 58,
            "height": 865,
            "width": 1512
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
def segmentation_inference(prediction_id_mapping):
    segmentation = prediction_id_mapping['superpixel'].copy()
    segmentation.update(
        {'mask': {
            'instanceURI': "sampleuri",
            'colorRGB': [0, 0, 0]
        }})
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
def text_inference(prediction_id_mapping):
    text = prediction_id_mapping['text'].copy()
    text.update({'answer': "free form text..."})
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


# also used for label imports
@pytest.fixture
def object_predictions(polygon_inference, rectangle_inference, line_inference,
                       entity_inference, segmentation_inference):
    return [
        polygon_inference, rectangle_inference, line_inference,
        entity_inference, segmentation_inference
    ]


@pytest.fixture
def classification_predictions(checklist_inference, text_inference):
    return [checklist_inference, text_inference]


@pytest.fixture
def predictions(object_predictions, classification_predictions):
    return object_predictions + classification_predictions


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
def model_run_with_model_run_data_rows(client, configured_project,
                                       model_run_predictions, model_run):
    configured_project.enable_model_assisted_labeling()

    upload_task = LabelImport.create_from_objects(
        client, configured_project.uid, f"label-import-{uuid.uuid4()}",
        model_run_predictions)
    upload_task.wait_until_done()
    label_ids = [label.uid for label in configured_project.labels()]
    model_run.upsert_labels(label_ids)
    time.sleep(3)
    yield model_run
    model_run.delete()
    # TODO: Delete resources when that is possible ..


@pytest.fixture
def model_run_with_all_project_labels(client, configured_project,
                                      model_run_predictions, model_run):
    configured_project.enable_model_assisted_labeling()

    upload_task = LabelImport.create_from_objects(
        client, configured_project.uid, f"label-import-{uuid.uuid4()}",
        model_run_predictions)
    upload_task.wait_until_done()
    model_run.upsert_labels(project_id=configured_project.uid)
    time.sleep(3)
    yield model_run
    model_run.delete()
    # TODO: Delete resources when that is possible ..


class AnnotationImportTestHelpers:

    @classmethod
    def assert_file_content(cls, url: str, predictions):
        response = requests.get(url)
        predictions = cls._convert_to_plain_object(predictions)
        assert ndjson.loads(response.text) == predictions

    @staticmethod
    def check_running_state(req, name, url=None):
        assert req.name == name
        if url is not None:
            assert req.input_file_url == url
        assert req.error_file_url is None
        assert req.status_file_url is None
        assert req.state == AnnotationImportState.RUNNING

    @staticmethod
    def _convert_to_plain_object(obj):
        """Some Python objects e.g. tuples can't be compared with JSON serialized data, serialize to JSON and deserialize to get plain objects"""
        json_str = ndjson.dumps(obj)
        return ndjson.loads(json_str)


@pytest.fixture
def annotation_import_test_helpers() -> Type[AnnotationImportTestHelpers]:
    return AnnotationImportTestHelpers()
