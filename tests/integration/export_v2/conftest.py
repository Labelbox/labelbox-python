import pytest
from labelbox.schema.queue_mode import QueueMode
from labelbox.schema.media_type import MediaType
from labelbox.schema.labeling_frontend import LabelingFrontend


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
