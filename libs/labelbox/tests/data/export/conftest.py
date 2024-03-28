import uuid
import time
import pytest
from labelbox.schema.queue_mode import QueueMode
from labelbox.schema.media_type import MediaType
from labelbox.schema.labeling_frontend import LabelingFrontend
from labelbox.schema.annotation_import import LabelImport, AnnotationImportState


@pytest.fixture
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


@pytest.fixture
def configured_project_with_ontology(client, initial_dataset, ontology,
                                     rand_gen, image_url):
    dataset = initial_dataset
    project = client.create_project(
        name=rand_gen(str),
        queue_mode=QueueMode.Batch,
    )
    editor = list(
        client.get_labeling_frontends(
            where=LabelingFrontend.name == "editor"))[0]
    project.setup(editor, ontology)
    data_row_ids = []

    for _ in range(len(ontology['tools']) + len(ontology['classifications'])):
        data_row_ids.append(dataset.create_data_row(row_data=image_url).uid)
    project.create_batch(
        rand_gen(str),
        data_row_ids,  # sample of data row objects
        5  # priority between 1(Highest) - 5(lowest)
    )
    project.data_row_ids = data_row_ids
    yield project
    project.delete()


@pytest.fixture
def configured_project_without_data_rows(client, ontology, rand_gen):
    project = client.create_project(name=rand_gen(str),
                                    description=rand_gen(str),
                                    queue_mode=QueueMode.Batch)
    editor = list(
        client.get_labeling_frontends(
            where=LabelingFrontend.name == "editor"))[0]
    project.setup(editor, ontology)
    yield project
    project.delete()


@pytest.fixture
def model_run_with_data_rows(client, configured_project_with_ontology,
                             model_run_predictions, model_run,
                             wait_for_label_processing):
    configured_project_with_ontology.enable_model_assisted_labeling()
    use_data_row_ids = [p['dataRow']['id'] for p in model_run_predictions]
    model_run.upsert_data_rows(use_data_row_ids)

    upload_task = LabelImport.create_from_objects(
        client, configured_project_with_ontology.uid,
        f"label-import-{uuid.uuid4()}", model_run_predictions)
    upload_task.wait_until_done()
    assert upload_task.state == AnnotationImportState.FINISHED, "Label Import did not finish"
    assert len(
        upload_task.errors
    ) == 0, f"Label Import {upload_task.name} failed with errors {upload_task.errors}"
    labels = wait_for_label_processing(configured_project_with_ontology)
    label_ids = [label.uid for label in labels]
    model_run.upsert_labels(label_ids)
    yield model_run, labels
    model_run.delete()
    # TODO: Delete resources when that is possible ..


@pytest.fixture
def model_run_predictions(polygon_inference, rectangle_inference,
                          line_inference):
    # Not supporting mask since there isn't a signed url representing a seg mask to upload
    return [polygon_inference, rectangle_inference, line_inference]


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
def prediction_id_mapping(configured_project_with_ontology):
    # Maps tool types to feature schema ids
    project = configured_project_with_ontology
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
                    "id": project.data_row_ids[idx],
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
                    "id": project.data_row_ids[idx],
                },
                'tool': tool
            }
    return result


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
