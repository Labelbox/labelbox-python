import uuid

import pytest
import time

from labelbox.schema.labeling_frontend import LabelingFrontend
from labelbox.schema.annotation_import import MALPredictionImport


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

    tools = [
        bbox_tool, polygon_tool, polyline_tool, point_tool, entity_tool,
        segmentation_tool
    ]
    classifications = [checklist, free_form_text]
    return {"tools": tools, "classifications": classifications}


@pytest.fixture
def configured_project(client, ontology, rand_gen, image_url):
    project = client.create_project(name=rand_gen(str))
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
def prediction_id_mapping(configured_project):
    #Maps tool types to feature schema ids
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
            "answer": {
                "schemaId":
                    rectangle['tool']['classifications'][0]['options'][0]
                    ['featureSchemaId']
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
def model_run_annotation_groups(client, configured_project,
                                annotation_submit_fn, model_run_predictions,
                                model_run):
    configured_project.enable_model_assisted_labeling()

    upload_task = MALPredictionImport.create_from_objects(
        client, configured_project.uid, f'mal-import-{uuid.uuid4()}',
        model_run_predictions)
    upload_task.wait_until_done()
    label_ids = []
    for data_row_id in {x['dataRow']['id'] for x in model_run_predictions}:
        label_ids.append(
            annotation_submit_fn(configured_project.uid, data_row_id))
    model_run.upsert_labels(label_ids)
    time.sleep(3)
    yield model_run
    # TODO: Delete resources when that is possible ..
