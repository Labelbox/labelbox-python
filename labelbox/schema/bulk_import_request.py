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
                        url: str) -> 'BulkImportRequest':
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
                            predictions: Iterable[dict]) -> 'BulkImportRequest':
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
        _validate_ndjson(predictions)
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
                    _validate_ndjson(reader)
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


When uploading a mask you can upload a single mask for all of the channels.
#Can you do which of the following?
#     - 1:1 label to mask
#     - 1:1 class per mask
#     - 1:1 image per mask (Looks like this one based on the doc but it is unclear...)
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
    
    
def get_valid_feature_schemas(client = None, project_id = "ckk4q1viuc0w107041siuht7p"):
    client = Client(api_key = os.environ.get("LABELBOX_TEST_API_KEY_PROD"))
    proj = client.get_project(project_id)
    ontology = proj.ontology()
    #print(ontology)
    valid_feature_schemas = {}
    for tool in ontology.normalized['tools']:
        classifications = [parse_classification(classification_tool) for classification_tool in tool['classifications']]
        valid_feature_schemas[tool['featureSchemaId']] = {'tool' : tool['tool'], 'classifications' : classifications}
        
    for tool in ontology.normalized['classifications']:
        valid_feature_schemas[tool['featureSchemaId']] = parse_classification(tool)
    return valid_feature_schemas


def validate_polygon(x):
    #TODO: Do we support multipolygons?
    assert len(x) >= 3, f"A polygon should be defined by at least 3 points. Found {len(x)}"
    for pt in x:
        assert len(pt.keys()) == 2
        assert 'x' in pt, 'y' in pt


def validate_line(x):
    #TODO: Do we support more than one at a time. Ie. line : [{...}, {...}] Our docs are unclear on this
    assert len(x) >= 2, f"A line should be defined by at least 2 points. Found {len(x)}"
    for pt in x:
        assert len(pt.keys()) == 2
        assert 'x' in pt, 'y' in pt    


def validate_point(x):
    #TODO: Do we support multipolygons?
    assert len(x.keys()) == 2
    assert 'x' in x, 'y' in x    
    #Do we want to check the type of the point. Looks like they should be ints.


def validate_text_location(x):
    assert len(x.keys()) == 2
    assert 'start' in x
    assert 'end' in x
    assert x['start'] <= x['end']
    

#TODO: Do we accept an index?
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
    assert len(x) == 128, f"Expected a uuid. Found {x}"

def validate_color(x):
    #Does the dtype matter? Can it be a float?
    if not isinstance(x, tuple, list):
        raise ValueError(f"Received color that is not a list or tuple. Found : {x}")
    elif len(x) != 3:
        raise ValueError(f"Must provide RGB values for segmentation colors. Found : {x}")
    elif not all([0 <= x_ <= 255 for x_ in x]):
        raise ValueError("All rgb colors must be between 0 and 255. Found : {x}")
    #We also want to make sure they are all different... todo

def is_string(x):
    assert type(x) == str

#Check if they named everything properly.
REQUIRED_KEYS =    {
                 "schema_id" : is_labelbox_id, #tool id
                   "uuid" : is_uuid,
                   "dataRow" : {"id" : is_labelbox_id}
}



def validate_nd_schema_ids(lines: Iterable[Dict[str, Any]] , client, project_id):
    proj = client.get_project(project_id)
    ontology = proj.ontology()
    valid_feature_schemas = get_valid_feature_schemas()
    for idx, line in enumerate(lines):
        if line['schema_id'] not in valid_feature_schemas:
            #Feature schema id must exist in project.ontology().normalized
            raise ValueError(f"Row {idx} has invalid feature schema_id. Found : {line['schema_id']}")

        #This means that this is a subclass
        if 'classifications' in line: 


def check_value(key, value):
    #Recursively check
    if isinstance(REQUIRED_KEYS[key], dict):
        for key_ in REQUIRED_KEYS[key]:
            _value = value.get(key_, "missing")
            if _value == "missing":
                raise ValueError("Expected key {required_key} for line {idx}")
            check_value(key_, _value)
    elif isinstance(REQUIRED_KEYS[key], callable):
        REQUIRED_KEYS[key](value)
    else:
        raise ValueError("Only support dicts and callables for value checking.")

def check_primary_keys(line):
    for key in REQUIRED_KEYS: check_value(key, line)



#Must have one of. Can it have more than one?
MUTUALLY_EXCLUSIVE_TOOLS = {
    'mask' : {"isinstanceURI" : is_uri, "colorRGB" : validate_color},
    'polygon' : validate_polygon,
    'point' : validate_point,
    'line' : validate_line,
    'location' : validate_text_location 
}

TOOL_KEYS = {
    'classifications' : {'radio' : {}, 'checklist' : [], 'text' : []}
}


MUTUALLY_EXCLUSIVE_CLASSIFICAITONS = {
    "answers" : [{"schemaId" : is_labelbox_id}], #checklist.
    "answer" : {is_string, {"schemaId" : is_labelbox_id}} #String for free-form test, dict for radio option.
}


def check_mutually_exclusive_group(group, tool):
    for key in group: check_value(key, tool)

def check_tools(line, feature_schemas):
    #Check top level
    unused_keys = set(line.keys()).difference(set(REQUIRED_KEYS.keys()))
    tool = feature_schemas[line["schema_id"]]
    
    #Check specific tool
    if tool in MUTUALLY_EXCLUSIVE_TOOLS:
        #top level tools
        if 'classifications' in unused_keys:
            for classification_tool in tool['classifications']:
                check_mutually_exclusive_group(MUTUALLY_EXCLUSIVE_CLASSIFICAITONS, classification_tool)      
        check_mutually_exclusive_group(MUTUALLY_EXCLUSIVE_TOOLS, tool)      

    else:
        #This case means we are working with classifications
        if 'classifications' in unused_keys:
            raise ValueError(f"classifications key is invalid for tools other than {MUTUALLY_EXCLUSIVE_TOOLS.keys()}")
        check_mutually_exclusive_group(MUTUALLY_EXCLUSIVE_CLASSIFICAITONS, tool)    

def _validate_ndjson(lines: Iterable[Dict[str, Any]], client, project_id) -> None:
    feature_schemas = get_valid_feature_schemas()
    _validate_uuids(lines)
    validate_nd_schema_ids(lines, client, project_id)
    for idx, line in enumerate(lines):
        #Check primary keys
        check_primary_keys(line)
        check_tools(line, feature_schemas)
        




    