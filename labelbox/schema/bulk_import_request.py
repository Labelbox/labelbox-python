import json
import logging
import time
from pathlib import Path
from typing import Any, Optional
from typing import BinaryIO
from typing import Dict
from typing import Iterable
from typing import Set
from typing import Tuple
from typing import Union

import backoff
import ndjson
import requests

from labelbox import utils
import labelbox.exceptions
from labelbox.orm import query
from labelbox.orm.db_object import DbObject
from labelbox.orm.model import Field
from labelbox.orm.model import Relationship
from labelbox.schema.enums import BulkImportRequestState

NDJSON_MIME_TYPE = "application/x-ndjson"
logger = logging.getLogger(__name__)



def _make_file_name(project_id: str, name: str) -> str:
    return f"{project_id}__{name}.ndjson"


# TODO(gszpak): move it to client.py
def _make_request_data(project_id: str, name: str, content_length: int,
                       file_name: str) -> dict:
    query_str = """mutation createBulkImportRequestFromFilePyApi(
            $projectId: ID!, $name: String!, $file: Upload!, $contentLength: Int!) {
        createBulkImportRequest(data: {
            projectId: $projectId,
            name: $name,
            filePayload: {
                file: $file,
                contentLength: $contentLength
            }
        }) {
            %s
        }
    }
    """ % query.results_query_part(BulkImportRequest)
    variables = {
        "projectId": project_id,
        "name": name,
        "file": None,
        "contentLength": content_length
    }
    operations = json.dumps({"variables": variables, "query": query_str})

    return {
        "operations": operations,
        "map": (None, json.dumps({file_name: ["variables.file"]}))
    }


# TODO(gszpak): move it to client.py
def _send_create_file_command(
        client, request_data: dict, file_name: str,
        file_data: Tuple[str, Union[bytes, BinaryIO], str]) -> dict:
    response = requests.post(
        client.endpoint,
        headers={"authorization": "Bearer %s" % client.api_key},
        data=request_data,
        files={file_name: file_data})

    try:
        response_json = response.json()
    except ValueError:
        raise labelbox.exceptions.LabelboxError(
            "Failed to parse response as JSON: %s" % response.text)

    response_data = response_json.get("data", None)
    if response_data is None:
        raise labelbox.exceptions.LabelboxError(
            "Failed to upload, message: %s" % response_json.get("errors", None))

    if not response_data.get("createBulkImportRequest", None):
        raise labelbox.exceptions.LabelboxError(
            "Failed to create BulkImportRequest, message: %s" %
            response_json.get("errors", None) or
            response_data.get("error", None))

    return response_data


class BulkImportRequest(DbObject):
    """Represents the import job when importing annotations.

    Attributes:
        name (str)
        state (Enum): FAILED, RUNNING, or FINISHED (Refers to the whole import job)
        input_file_url (str): URL to your web-hosted NDJSON file
        error_file_url (str): NDJSON that contains error messages for failed annotations
        status_file_url (str): NDJSON that contains status for each annotation
        created_at (datetime): UTC timestamp for date BulkImportRequest was created

        project (Relationship): `ToOne` relationship to Project
        created_by (Relationship): `ToOne` relationship to User
    """
    name = Field.String("name")
    state = Field.Enum(BulkImportRequestState, "state")
    input_file_url = Field.String("input_file_url")
    error_file_url = Field.String("error_file_url")
    status_file_url = Field.String("status_file_url")
    created_at = Field.DateTime("created_at")

    project = Relationship.ToOne("Project")
    created_by = Relationship.ToOne("User", False, "created_by")

    def refresh(self) -> None:
        """Synchronizes values of all fields with the database.
        """
        query_str, params = query.get_single(BulkImportRequest, self.uid)
        res = self.client.execute(query_str, params)
        res = res[utils.camel_case(BulkImportRequest.type_name())]
        self._set_field_values(res)

    def wait_until_done(self, sleep_time_seconds: int = 30) -> None:
        """Blocks import job until certain conditions are met.

        Blocks until the BulkImportRequest.state changes either to
        `BulkImportRequestState.FINISHED` or `BulkImportRequestState.FAILED`,
        periodically refreshing object's state.

        Args:
            sleep_time_seconds (str): a time to block between subsequent API calls
        """
        while self.state == BulkImportRequestState.RUNNING:
            logger.info(f"Sleeping for {sleep_time_seconds} seconds...")
            time.sleep(sleep_time_seconds)
            self.__exponential_backoff_refresh()

    @backoff.on_exception(
        backoff.expo,
        (labelbox.exceptions.ApiLimitError, labelbox.exceptions.TimeoutError,
         labelbox.exceptions.NetworkError),
        max_tries=10,
        jitter=None)
    def __exponential_backoff_refresh(self) -> None:
        self.refresh()

    @classmethod
    def from_name(cls, client, project_id: str,
                  name: str) -> 'BulkImportRequest':
        """ Fetches existing BulkImportRequest.

        Args:
            client (Client): a Labelbox client
            project_id (str): BulkImportRequest's project id
            name (str): name of BulkImportRequest
        Returns:
            BulkImportRequest object

        """
        query_str = """query getBulkImportRequestPyApi(
                $projectId: ID!, $name: String!) {
            bulkImportRequest(where: {
                projectId: $projectId,
                name: $name
            }) {
                %s
            }
        }
        """ % query.results_query_part(cls)
        params = {"projectId": project_id, "name": name}
        response = client.execute(query_str, params=params)
        return cls(client, response['bulkImportRequest'])

    @classmethod
    def create_from_url(cls, client, project_id: str, name: str,
                        url: str, validate = True) -> 'BulkImportRequest':
        """
        Creates a BulkImportRequest from a publicly accessible URL
        to an ndjson file with predictions.

        Args:
            client (Client): a Labelbox client
            project_id (str): id of project for which predictions will be imported
            name (str): name of BulkImportRequest
            url (str): publicly accessible URL pointing to ndjson file containing predictions
        Returns:
            BulkImportRequest object
        """
        if validate:
            logger.warn("Validation is turned on. The file will be downloaded locally and processed before uploading.")                
            res = requests.get(url)
            data = ndjson.loads(res.text)
            _validate_ndjson(data, client.get_project(project_id))
            

        query_str = """mutation createBulkImportRequestPyApi(
                $projectId: ID!, $name: String!, $fileUrl: String!) {
            createBulkImportRequest(data: {
                projectId: $projectId,
                name: $name,
                fileUrl: $fileUrl
            }) {
                %s
            }
        }
        """ % query.results_query_part(cls)
        params = {"projectId": project_id, "name": name, "fileUrl": url}
        bulk_import_request_response = client.execute(query_str, params=params)
        return cls(client,
                   bulk_import_request_response["createBulkImportRequest"])

    @classmethod
    def create_from_objects(cls, client, project_id: str, name: str,
                            predictions: Iterable[dict], validate = True) -> 'BulkImportRequest':
        """
        Creates a `BulkImportRequest` from an iterable of dictionaries.

        Conforms to JSON predictions format, e.g.:
        ``{
            "uuid": "9fd9a92e-2560-4e77-81d4-b2e955800092",
            "schemaId": "ckappz7d700gn0zbocmqkwd9i",
            "dataRow": {
                "id": "ck1s02fqxm8fi0757f0e6qtdc"
            },
            "bbox": {
                "top": 48,
                "left": 58,
                "height": 865,
                "width": 1512
            }
        }``

        Args:
            client (Client): a Labelbox client
            project_id (str): id of project for which predictions will be imported
            name (str): name of BulkImportRequest
            predictions (Iterable[dict]): iterable of dictionaries representing predictions
        Returns:
            BulkImportRequest object
        """
        if validate:
            _validate_ndjson(predictions, client.get_project(project_id))

        data_str = ndjson.dumps(predictions)
        if not data_str:
            raise ValueError('annotations cannot be empty')

        data = data_str.encode('utf-8')
        file_name = _make_file_name(project_id, name)
        request_data = _make_request_data(project_id, name, len(data_str),
                                          file_name)
        file_data = (file_name, data, NDJSON_MIME_TYPE)
        response_data = _send_create_file_command(client,
                                                  request_data=request_data,
                                                  file_name=file_name,
                                                  file_data=file_data)

        return cls(client, response_data["createBulkImportRequest"])

    @classmethod
    def create_from_local_file(cls,
                               client,
                               project_id: str,
                               name: str,
                               file: Path,
                               validate_file=True) -> 'BulkImportRequest':
        """
        Creates a BulkImportRequest from a local ndjson file with predictions.

        Args:
            client (Client): a Labelbox client
            project_id (str): id of project for which predictions will be imported
            name (str): name of BulkImportRequest
            file (Path): local ndjson file with predictions
            validate_file (bool): a flag indicating if there should be a validation
                if `file` is a valid ndjson file
        Returns:
            BulkImportRequest object

        """
        file_name = _make_file_name(project_id, name)
        content_length = file.stat().st_size
        request_data = _make_request_data(project_id, name, content_length,
                                          file_name)

        with file.open('rb') as f:
            if validate_file:
                reader = ndjson.reader(f)
                # ensure that the underlying json load call is valid
                # https://github.com/rhgrant10/ndjson/blob/ff2f03c56b21f28f7271b27da35ca4a8bf9a05d0/ndjson/api.py#L53
                # by iterating through the file so we only store
                # each line in memory rather than the entire file
                try:
                    _validate_ndjson(reader, client.get_project(project_id))
                except ValueError:
                    raise ValueError(f"{file} is not a valid ndjson file")
                else:
                    f.seek(0)
            file_data = (file.name, f, NDJSON_MIME_TYPE)
            response_data = _send_create_file_command(client, request_data,
                                                      file_name, file_data)
        return cls(client, response_data["createBulkImportRequest"])


"""     
#Outstanding questions:

* How to check data row media type?
    * Video
        - annotations without frames indices wouldn't be flagged right now
    * Everything else
        - We won't know if a text tool is being used for video. 
        - Or a tool only support for images is being used for video
        ... etc

- video only supports radio and checklist tools. 
    - This would be good to validate here.

* While this is a pretty decent check it isn't going to be 100% since we aren't examining the actual data rows.
* Eg entity recognition we can't check if the index is greater than the doc length.


"""

def _validate_uuids(lines: Iterable[Dict[str, Any]]) -> None:
    """Validate individual ndjson lines.
        - verifies that uuids are unique
    """
    uuids: Set[str] = set()
    for line in lines:
        uuid = line['uuid']
        if uuid in uuids:
            raise labelbox.exceptions.UuidError(
                f'{uuid} already used in this import job, '
                'must be unique for the project.')
        uuids.add(uuid)

def parse_classification(tool):
    """
    Only radio, checklist, and text are supported for mal
    """
    if tool['type'] in ['radio', 'checklist']:
        return {'tool' : tool['type'], 'featureSchemaId' : tool['featureSchemaId'] , 'options' : [r['featureSchemaId'] for r in tool['options']]}
    elif tool['type'] == 'text':
        return {'tool' : tool['type'],  'featureSchemaId' : tool['featureSchemaId']}
    #Other subtypes not supported
    
def get_valid_feature_schemas(project):
    ontology = project.ontology()
    #print(ontology)
    valid_feature_schemas = {}
    for tool in ontology.normalized['tools']:
        classifications = [parse_classification(classification_tool) for classification_tool in tool['classifications']]
        classifications = {v['featureSchemaId'] : v for v in classifications}
        valid_feature_schemas[tool['featureSchemaId']] = {'tool' : tool['tool'], 'classifications' : classifications}
    for tool in ontology.normalized['classifications']:
        valid_feature_schemas[tool['featureSchemaId']] = parse_classification(tool)
    return valid_feature_schemas

def validate_polygon(x):
    #TODO: Do we support multipolygons?
    if not isinstance(x, list):
        raise TypeError(f"Polygon should be a list of dicts with 'x', 'y' keys. Found {type(x)}")

    if len(x) < 4:
        raise ValueError(f"A polygon should be defined by at least 3 points. Found {len(x)}, {x}")
    for pt in x:
        for key in pt:
            if key not in ['x', 'y']:
                raise ValueError(f"Point is missing : {key}")
        if len(pt.keys()) != 2:
            raise ValueError(f"Expects {'x', 'y'} pair. Found : {pt}")
        
def validate_line(x):
    if not isinstance(x, list):
        raise TypeError(f"Lines should be a list of dicts with 'x', 'y' keys. Found {type(x)}")

    if len(x) < 2:
        raise ValueError(f"A line should be defined by at least 2 points. Found {len(x)}, {x}")

    for pt in x:
        for coord_name in pt:
            if coord_name not in ['x', 'y']:
                raise ValueError(f"Point is missing : {coord_name}")
        if len(pt.keys()) != 2:
            raise ValueError(f"Expects {'x', 'y'} pair. Found : {pt}")
          
def validate_rectangle(x):
    required_keys = ["top", "left", "height", "width"]
    for key in required_keys:
        if  key not in x:
            raise ValueError(f"Rectangle missing required key : {key}")
        
        if not isinstance(x[key], int):
            raise ValueError(f"rectangle must be provided ints. Found {x[key]} for {key}")

def validate_point(x):
    #TODO: Do we support multipolygons?
    for coord_name in x:
        if coord_name not in ['x', 'y']:
            raise ValueError(f"Point is missing : {coord_name}")
    #Do we want to check the type of the point. Should be ints?

def validate_text_location(x):
    if 'start' not in x:
        raise ValueError(f"Must include a start key for entity. Found : {x}")
    if 'end' not in x:
        raise ValueError(f"Must include a start key for entity. Found : {x}")    
    if len(x.keys()) != 2:
        raise ValueError(f"Only start and end are valid. Found : {x}")
    if not x['start'] <= x['end']:
        raise ValueError(f"Start must be less than or equal to end. Found : {x}")
    if not x['start'] >= 0:
        #TODO: Is this zero indexed? 
        raise ValueError(f"Start must be greater than or equal to 0. Found : {x}")
    
def is_uri(x):
    #simple for now
    if not isinstance(x, str):
        raise ValueError(f"Expected a uri. Found {x}")


def is_labelbox_id(x):
    #simple for now
    if not isinstance(x, str):
        raise ValueError(f"Expected a labelbox_id. Found {x}")

def is_uuid(x):
    #simple for now
    if not isinstance(x, str):
        raise ValueError(f"Expected a uuid. Found {x}")
    
    if len(x) != 36:
        #Wrong type..
        raise ValueError(f"Expected a uuid. Found {x}")

def validate_color(x):
    #Does the dtype matter? Can it be a float?
    if not isinstance(x, (tuple, list)):
        raise ValueError(f"Received color that is not a list or tuple. Found : {x}")
    elif len(x) != 3:
        raise ValueError(f"Must provide RGB values for segmentation colors. Found : {x}")
    elif not all([0 <= x_ <= 255 for x_ in x]):
        raise ValueError("All rgb colors must be between 0 and 255. Found : {x}")
    #We also want to make sure they are all different... todo

def is_string(x):
    if type(x) != str:
        raise TypeError(f"Expected {x} to be a string.")


def check_value(required_dict, payload_dict, **kwargs):
    #Won't work for lists.
    for key in required_dict:
        if key not in payload_dict:
            raise ValueError(f"Expected {key} to be in the payload : {payload_dict}.")
        if callable(required_dict[key]):
            required_dict[key](payload_dict[key], **kwargs)
        elif isinstance(required_dict[key] , dict):
            if type(required_dict[key]) != type(payload_dict[key]):
                raise TypeError("Both must be lists or dicts")
            check_value(required_dict[key], payload_dict[key], **kwargs)
        else:
            ValueError(f"required dict has unexpected type : {required_dict[key]}")


def check_answer(x, valid_schemas):
    #TODO: Is dict the best way to handle this?
    if isinstance(x, dict):
        #TODO: Fix this...
        schema = x['schemaId']
        is_labelbox_id(schema)
        if schema not in valid_schemas:
            #The schema for this tool does not match what is in the editor
            raise ValueError(f"schema {schema} not in allowed schemas {valid_schemas}")
    else:
        #Free form text
        is_string(x)

def check_answers(x, valid_schemas):
    if not len(x):
        raise ValueError(f"Must provide at least one answer to upload. Found {x}. Valid options {valid_schemas}") #TODO: Is it ok to submit an empty list of answers? Or should you just not enter anything?
    
    schemas = [x_.get('schemaId') for x_ in x]
    if None in schemas:
        raise ValueError(f"Found answer without id. {x}. Must be one of {valid_schemas}")


    if len(schemas) != len(set(schemas)):
        raise ValueError(f"schemas for an example must be unique. Found {schemas}")
    for schema in schemas:
        is_labelbox_id(schema)
        if schema not in valid_schemas:
            raise ValueError(f"schema {schema} not in allowed schemas {valid_schemas}")


#Check if they named everything properly.
REQUIRED_KEYS =    {
                 "schemaId" : is_labelbox_id, #tool id
                   "uuid" : is_uuid,
                   "dataRow" : {"id" : is_labelbox_id}
}

TOOL_MAPPINGS = {
    'rectangle' : 'bbox',
    'named-entity' : 'location',
    'superpixel' : 'mask'
}

CLASSIFICATION_MAPPINGS = {
    'radio' : 'answer',
    'text' : 'answer',
    'checklist' : 'answers'
}

MUTUALLY_EXCLUSIVE_TOOLS = {
    'mask' : {"instanceURI" : is_uri, "colorRGB" : validate_color},
    'polygon' : validate_polygon,
    'point' : validate_point,
    'line' : validate_line,
    'location' : validate_text_location ,
    'bbox' : validate_rectangle,
}

MUTUALLY_EXCLUSIVE_CLASSIFICAITONS = {
    "answers" : check_answers,
    "answer" : check_answer 
}

def check_tools(line, feature_schemas):
    #Check top level
    unused_keys = set(line.keys()).difference(set(REQUIRED_KEYS.keys()))

    if line["schemaId"] not in feature_schemas:
        raise ValueError(f"Invalid feature schemaId. Found : {line['schemaId']}")
    tool = feature_schemas[line["schemaId"]]
    ####TODO: check that the tool in the unused key: assert tool == unused_keys. We prob need a mapping for this..

    #Are we checking for valid feature schemas for sub classes?

    if tool['tool'] in MUTUALLY_EXCLUSIVE_TOOLS or TOOL_MAPPINGS.get(tool["tool"]) is not None:
        #top level tools
        if 'classifications' in unused_keys:
            #TODO: We need to only loop over one of these and grab the other..
            #This will throw an error if there is more than 1 of each!!!!
            #TODO
            """
            #TODO
            #TODO
            #TODO
            #TODO
            """
            for classification_tool in tool['classifications'].values():
                for classification_line in line['classifications']:
                    check_value(
                        {
                            CLASSIFICATION_MAPPINGS.get(classification_tool["tool"], 
                            classification_tool['tool']) : MUTUALLY_EXCLUSIVE_CLASSIFICAITONS[CLASSIFICATION_MAPPINGS.get(classification_tool["tool"], 
                            classification_tool['tool'])]
                        }, 
                        classification_line,
                        valid_schemas = classification_tool.get('options')
                    )    
                    if classification_line["schemaId"] not in tool['classifications']:
                        raise ValueError(f"Invalid feature schemaId. Found : {line['schemaId']}")
                    
                    #TODO: Check individual classifications
                    ###Classifications are harder.. unused_keys = set(CLASSIFICATION_MAPPINGS.get(classification_tool["tool"], classification_tool['tool'])).difference(unused_keys)
                unused_keys.remove('classifications')
        check_value({TOOL_MAPPINGS.get(tool["tool"], tool['tool']) : MUTUALLY_EXCLUSIVE_TOOLS[TOOL_MAPPINGS.get(tool["tool"], tool['tool'])]}, line)   
        unused_keys = unused_keys.difference(set({TOOL_MAPPINGS.get(tool["tool"], tool['tool'])}))
    else:
        #This case means we are working with classifications
        if 'classifications' in unused_keys:
            raise ValueError(f"classifications key is invalid for tools other than {MUTUALLY_EXCLUSIVE_TOOLS.keys()}")

        check_value(
            {
                CLASSIFICATION_MAPPINGS.get(tool["tool"], tool['tool']) : MUTUALLY_EXCLUSIVE_CLASSIFICAITONS[CLASSIFICATION_MAPPINGS.get(tool["tool"], tool['tool'])]
            }, 
                line,
                valid_schemas = tool.get('options')
            )   
        unused_keys = unused_keys.difference(set({CLASSIFICATION_MAPPINGS.get(tool["tool"], tool['tool'])}))

    if len(unused_keys) > 0:
        #This is likely due to the user trying to upload more than one tool type for a single line.
        raise ValueError(f"Found unused keys {line.keys()}\nSet of unused keys : {unused_keys}")
    
def validate_datarow(line, data_row_ids):
    if line['dataRow']['id'] not in data_row_ids:
        raise ValueError(f"Uploading data to data row that does not exist in the project. data_row id: {line['dataRow']['id']}")


def _validate_ndjson(lines: Iterable[Dict[str, Any]], project) -> None:
    data_row_ids = {data_row.uid : data_row for dataset in project.datasets() for data_row in dataset.data_rows()}
    feature_schemas = get_valid_feature_schemas(project)
    _validate_uuids(lines)
    for idx, line in enumerate(lines):
        #Check primary keys
        try:
            check_value(REQUIRED_KEYS, line)
            validate_datarow(line , data_row_ids)
            check_tools(line, feature_schemas)
        except Exception as e:
            raise type(e)(f"Error on line {idx}") from e


#def ValidatorFactory(line):


"""
from pydantic import BaseModel

#How do I add subclasses?
#What is valid?
#Here is your answer :)


class MALRow(BaseModel):
    tools: List
    classifications: List


class MALValidator(BaseModel):
    schemaId: 
    uuid: 
    #Todo what is the pydantic type for this? dataRow:                "dataRow" : {"id" : is_labelbox_id}

class Classification(MALValidator):
    tool : #Enum (supported set of tools)
    feature_schema_id:  #(labelbox id)

class Text():

class 

class Tool(MALValidator):


class Geometry(BaseModel):
class Bbox(Geometry):
class Mask(Geometry):
class Point(Geometry):

class Line(Geometry):


class 
"""
