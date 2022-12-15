from typing import Any, List, Optional, TypedDict, Union
import os

from labelbox_dev.entity import Entity
from labelbox_dev.exceptions import LabelboxError
from labelbox_dev.session import Session
from labelbox_dev.task import DataRowImportTask

DATA_ROW_RESOURCE = "data-rows"


class AttachmentsType(TypedDict):
    type: str
    value: str
    name: str


class MetadataType(TypedDict):
    schema_id: str
    value: Any


class CreateDataRowType(TypedDict):
    id: Optional[str]
    global_key: Optional[str]
    external_id: Optional[str]
    row_data: str
    attachments: List[AttachmentsType]
    metadata: List[MetadataType]
    media_type: Optional[str]


class UpdateDataRowType(TypedDict):
    global_key: Optional[str]
    external_id: Optional[str]
    row_data: Optional[str]

def validate_keys(item):
    if 'row_data' not in item:
        raise LabelboxError("`row_data` missing when creating DataRow.")

def format_data_rows(data_rows):
    for data_row in data_rows:

        validate_keys(data_row)

        # handle the case when data_row.row_data is a file
        if os.path.exists(data_row['row_data']):

            # TODO. consider uploading file instead
            with open(data_row['row_data'], "r") as f:
                data_row['row_data'] = f.read()

            if not data_row.get('external_id'):
                data_row['external_id'] = data_row['row_data']

    return data_rows

def get_by_id(data_row_id: str):
    data_row_json = Session.get_request(f"{DATA_ROW_RESOURCE}/{data_row_id}")
    return DataRow(data_row_json)


def get_by_global_key(global_key: str):
    params = {'is_global_key': True}
    data_row_json = Session.get_request(f"{DATA_ROW_RESOURCE}/{global_key}",
                                        params)
    return DataRow(data_row_json)


def get_by_ids(data_row_ids):
    # TODO: Bulk fetching by ids
    pass


def get_by_global_keys(global_keys):
    # TODO: Bulk fetching by global keys
    pass


def create_one(dataset_id, data_row: CreateDataRowType):

    data_rows = format_data_rows(data_rows)

    create_data_row_input = {
        'dataset_id': dataset_id,
        'data_row': data_row
    }

    data_row_json = Session.post_request(f"{DATA_ROW_RESOURCE}",
                                         json=create_data_row_input)
    return DataRow(data_row_json)


def create(dataset_id,
           data_rows: List[CreateDataRowType],
           run_async: bool = False):

    data_rows = format_data_rows(data_rows)

    create_data_rows_input = {
        'dataset_id': dataset_id,
        'data_rows': data_rows,
        'run_async': run_async
    }

    if run_async:
        task_json = Session.post_request(f"{DATA_ROW_RESOURCE}/bulkcreate",
                                         json=create_data_rows_input)
        task_id = task_json.get(
            'taskId')  # TODO: change to snake_case from backend

        if task_id is None:
            raise LabelboxError(
                f"Failed to retrieve task information for `data_row.create()` async operation"
            )
        return DataRowImportTask.get_by_id(task_id)

    # TODO: Need to paginate sync call. Currently, 100 data rows is the limit
    data_rows = Session.post_request(f"{DATA_ROW_RESOURCE}/bulkcreate",
                                     json=create_data_rows_input)
    return [DataRow(data_row_json) for data_row_json in data_rows]


class DataRow(Entity):

    def __init__(self, json):
        super().__init__(json)
        self.from_json(json)

    def from_json(self, json) -> "DataRow":
        super().from_json(json)
        self.id = self.json['id']
        self.global_key = self.json['global_key']
        self.external_id = self.json['external_id']
        self.created_at = self.json['created_at']
        self.updated_at = self.json['updated_at']
        self.row_data = self.json['row_data']
        self.dataset_id = self.json['dataset_id']
        self.created_by_id = self.json['created_by_id']
        self.organization_id = self.json['organization_id']
        self.attachments = self.json['attachments']
        self.metadata = self.json['metadata']

        return self

    def delete(self) -> None:
        Session.delete_request(f"{DATA_ROW_RESOURCE}/{self.id}")

    def update(self, data_row_update: UpdateDataRowType) -> "DataRow":
        data_row_json = Session.patch_request(f"{DATA_ROW_RESOURCE}/{self.id}",
                                              json=data_row_update)
        return self.from_json(data_row_json)
