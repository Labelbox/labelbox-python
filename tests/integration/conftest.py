from collections import namedtuple
from enum import Enum
from datetime import datetime
from labelbox.schema.labeling_frontend import LabelingFrontend
import os
from random import randint
import re
from string import ascii_letters
import uuid
import pytest

from labelbox import Client

IMG_URL = "https://picsum.photos/200/300"


class Environ(Enum):
    PROD = 'prod'
    STAGING = 'staging'


@pytest.fixture
def environ() -> Environ:
    """
    Checks environment variables for LABELBOX_ENVIRON to be
    'prod' or 'staging'

    Make sure to set LABELBOX_TEST_ENVIRON in .github/workflows/python-package.yaml

    """
    try:
        return Environ(os.environ['LABELBOX_TEST_ENVIRON'])
    except KeyError:
        raise Exception(f'Missing LABELBOX_TEST_ENVIRON in: {os.environ}')


def graphql_url(environ: str) -> str:
    if environ == Environ.PROD:
        return 'https://api.labelbox.com/graphql'
    return 'https://staging-api.labelbox.com/graphql'


def testing_api_key(environ: str) -> str:
    if environ == Environ.PROD:
        return os.environ["LABELBOX_TEST_API_KEY_PROD"]
    return os.environ["LABELBOX_TEST_API_KEY_STAGING"]


class IntegrationClient(Client):

    def __init__(self, environ: str) -> None:
        api_url = graphql_url(environ)
        api_key = testing_api_key(environ)
        super().__init__(api_key, api_url)

        self.queries = []

    def execute(self, query, params=None, check_naming=True, **kwargs):
        if check_naming:
            assert re.match(r"(?:query|mutation) \w+PyApi", query) is not None
        self.queries.append((query, params))
        return super().execute(query, params, **kwargs)


@pytest.fixture
def client(environ: str):
    return IntegrationClient(environ)


@pytest.fixture
def rand_gen():
    def gen(field_type):
        if field_type is str:
            return "".join(ascii_letters[randint(0,
                                                 len(ascii_letters) - 1)]
                           for _ in range(16))

        if field_type is datetime:
            return datetime.now()

        raise Exception("Can't random generate for field type '%r'" %
                        field_type)

    return gen


@pytest.fixture
def project(client, rand_gen):
    project = client.create_project(name=rand_gen(str))
    yield project
    project.delete()


@pytest.fixture
def dataset(client, rand_gen):
    dataset = client.create_dataset(name=rand_gen(str))
    yield dataset
    dataset.delete()


LabelPack = namedtuple("LabelPack", "project dataset data_row label")


@pytest.fixture
def label_pack(project, rand_gen):
    client = project.client
    dataset = client.create_dataset(name=rand_gen(str), projects=project)
    data_row = dataset.create_data_row(row_data=IMG_URL)
    label = project.create_label(data_row=data_row, label=rand_gen(str))
    yield LabelPack(project, dataset, data_row, label)
    dataset.delete()


@pytest.fixture
def iframe_url(environ) -> str:
    if environ == Environ.PROD:
        return 'https://editor.labelbox.com'
    return 'https://staging.labelbox.dev/editor'


@pytest.fixture
def sample_video() -> str:
    path_to_video = 'tests/integration/media/cat.mp4'
    assert os.path.exists(path_to_video)
    return path_to_video

@pytest.fixture
def ontology():
    bbox_tool = {'required': False, 'name': 'bbox', 'tool': 'rectangle', 'color': '#a23030', 'classifications' : [
        {
            'required': False, 'instructions': 'nested', 'name': 'nested', 'type': 'radio', 'options': [
                    {
                        'label': 'radio_option_1', 'value': 'radio_value_1'
                    }
            ]
        }
    ]}
    polygon_tool = {'required': False, 'name': 'polygon', 'tool': 'polygon', 'color': '#FF34FF', 'classifications' : []}
    polyline_tool = {'required': False, 'name': 'polyline', 'tool': 'line', 'color': '#FF4A46', 'classifications': []}
    point_tool = {'required': False, 'name': 'point--', 'tool': 'point', 'color': '#008941', 'classifications': []}
    entity_tool = {'required': False, 'name': 'entity--', 'tool': 'named-entity', 'color': '#006FA6', 'classifications': []}
    segmentation_tool = {'required': False, 'name': 'segmentation--', 'tool': 'superpixel', 'color': '#A30059', 'classifications': []}
    checklist =     {'required': False, 'instructions': 'checklist', 'name': 'checklist', 'type': 'checklist', 'options': [{'label': 'option1', 'value': 'option1'}, {'label': 'option2', 'value': 'option2'}, {'label': 'optionN', 'value': 'optionn'}]}
    free_form_text = {'required': False, 'instructions': 'text', 'name': 'text', 'type': 'text', 'options': []}

    ####Why does this break?
    #Adding radio buttons causes the whole ontology to be invalid..
    #radio_buttons = {'required': False, 'instructions': 'radio_tool',  'name': 'radio_tool', 'type': 'radio', 'options': [{'label': 'yes', 'value': 'yes'}, {'label': 'no', 'value': 'no'}]}, 
    #ontology = {"tools": [bbox_tool, polygon_tool, polyline_tool, point_tool, entity_tool, segmentation_tool], "classifications": [radio_buttons, checklist, free_form_text]}
    ####
    tools = [bbox_tool, polygon_tool, polyline_tool, point_tool, entity_tool, segmentation_tool]
    classifications = [checklist, free_form_text]
    return {"tools" : tools, "classifications" : classifications}


@pytest.fixture
def configured_project(client, rand_gen, ontology):
    project = client.create_project(name=rand_gen(str))
    editor = list(
        client.get_labeling_frontends(
            where=LabelingFrontend.name == "editor"))[0]
    project.setup(editor, ontology)
    dataset = client.create_dataset(name = rand_gen(str))
    for _ in range(len(ontology['tools']) + len(ontology['classifications'])):
        dataset.create_data_row(row_data=IMG_URL)
    project.datasets.connect(dataset)
    yield project
    project.delete()
    dataset.delete()



@pytest.fixture
def prediction_id_mapping(configured_project):
    #Maps tool types to feature schema ids
    ontology = configured_project.ontology().normalized
    inferences = []
    datarows = [d for d in list(configured_project.datasets())[0].data_rows()]
    result = {}
    
    for idx, tool in enumerate(ontology['tools'] + ontology['classifications']):
        if 'tool' in tool:
            tool_type = tool['tool']
        else:
            tool_type = tool['type']
        result[tool_type] = {
            "uuid" : str(uuid.uuid4()),
            "schemaId": tool['featureSchemaId'],
            "dataRow": {
                "id": datarows[idx].uid,
            },
            'tool' : tool
        }
    return result
            

@pytest.fixture
def polygon_inference(prediction_id_mapping):
    polygon = prediction_id_mapping['polygon']
    polygon.update(
{
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
            }
    )
    del polygon['tool']
    return polygon

@pytest.fixture
def rectangle_inference(prediction_id_mapping):
    rectangle = prediction_id_mapping['rectangle']
    rectangle.update( {"bbox": {
                    "top": 48,
                    "left": 58,
                    "height": 865,
                    "width": 1512
                },
                'classifications' : [{
                     "schemaId" : rectangle['tool']['classifications'][0]['featureSchemaId'],
                     "answer": {"schemaId": rectangle['tool']['classifications'][0]['options'][0]['featureSchemaId'] }
                }]
            })
    del rectangle['tool']
    return rectangle

@pytest.fixture
def line_inference(prediction_id_mapping):
    line = prediction_id_mapping['line']
    line.update({
                    "line": [{
                    "x": 147.692,
                    "y": 118.154
                },
                {
                    "x": 150.692,
                    "y": 160.154
                }]
            })
    del line['tool']            
    return line

@pytest.fixture
def point_inference(prediction_id_mapping):
    point = prediction_id_mapping['point']
    point.update({
        "point": {
                    "x": 147.692,
                    "y": 118.154
                }}
    )
    del point['tool']    
    return point

@pytest.fixture
def entity_inference(prediction_id_mapping):
    entity = prediction_id_mapping['named-entity']
    entity.update({"location" : {
                "start" : 67,
                "end" : 128
            }})
    del entity['tool']                
    return entity

@pytest.fixture
def segmentation_inference(prediction_id_mapping):
    segmentation = prediction_id_mapping['superpixel']
    segmentation.update({'mask' : {
                'instanceURI' : "sampleuri",
                'colorRGB' : [0,0,0]
            }
            })
    del segmentation['tool']             
    return segmentation        

@pytest.fixture
def checklist_inference(prediction_id_mapping):
    checklist = prediction_id_mapping['checklist']
    checklist.update({'answers' : [
                    {
                        'schemaId' : checklist['tool']['options'][0]['featureSchemaId']
                    }
                ]
            })
    del checklist['tool']              
    return checklist    

@pytest.fixture
def text_inference(prediction_id_mapping):
    text = prediction_id_mapping['text']
    text.update({
                'answer' : "free form text..."
  
            })
    del text['tool']
    return text   

@pytest.fixture
def predictions(polygon_inference,
              rectangle_inference, 
              line_inference, 
              entity_inference,
               segmentation_inference,
                checklist_inference,
                 text_inference):
    return [
        polygon_inference,
        rectangle_inference,
        line_inference,
        entity_inference,
        segmentation_inference,
        checklist_inference,
        text_inference
    ]
    