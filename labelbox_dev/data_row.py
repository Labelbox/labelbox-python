import os
from typing import Any, Iterator, List, Optional

from labelbox_dev.entity import Entity
from labelbox_dev.exceptions import LabelboxError
from labelbox_dev.session import Session
from labelbox_dev.task import CreateDataRowsTask, DeleteDataRowsTask, UpdateDataRowsTask
from labelbox_dev.types import TypedDict
from labelbox_dev.pagination import IdentifierPaginator

DATA_ROW_RESOURCE = "data-rows"
MAX_SYNCHRONOUS_DATA_ROW_REQUEST = 100  # Tentatively set to 100


class AttachmentsInput(TypedDict):
    type: str
    value: str
    name: str


class MetadataInput(TypedDict):
    schema_id: str
    value: Any


class CreateDataRowInput(TypedDict):
    id: Optional[str]
    global_key: Optional[str]
    external_id: Optional[str]
    row_data: str
    attachments: List[AttachmentsInput]
    metadata: List[MetadataInput]
    media_type: Optional[str]


class UpdateDataRowInput(TypedDict):
    id: Optional[str]
    global_key: Optional[str]
    external_id: Optional[str]
    row_data: Optional[str]


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

    @staticmethod
    def _validate_keys(item):
        if 'row_data' not in item:
            raise LabelboxError("`row_data` missing when creating DataRow.")

    @staticmethod
    def _format_data_rows(data_rows):
        for data_row in data_rows:
            DataRow._validate_keys(data_row)

            # handle the case when data_row.row_data is a file
            if os.path.exists(data_row['row_data']):
                filepath = data_row['row_data']
                # TODO. consider uploading file to gcs instead
                with open(data_row['row_data'], "r") as f:
                    data_row['row_data'] = f.read()

                if not data_row.get('external_id'):
                    data_row['external_id'] = filepath
        return data_rows

    @staticmethod
    def _check_sync_request_limits(request_name: str, request_count):
        if request_count > MAX_SYNCHRONOUS_DATA_ROW_REQUEST:
            raise LabelboxError(
                f"Request exceeds {MAX_SYNCHRONOUS_DATA_ROW_REQUEST} DataRows. Please use `DataRow.{request_name}_async()` instead"
            )

    @staticmethod
    def create_async(dataset_id,
                     data_rows: List[CreateDataRowInput]) -> CreateDataRowsTask:
        data_rows = DataRow._format_data_rows(data_rows)
        body = {
            'dataset_id': dataset_id,
            'data_rows': data_rows,
        }

        task_json = Session.post_request(f"{DATA_ROW_RESOURCE}/create-async",
                                         json=body)
        task_id = task_json.get(
            'taskId')  # TODO: change to snake_case from backend
        if task_id is None:
            raise LabelboxError(
                f"Failed to retrieve task information for `data_row.create()` async operation"
            )
        return CreateDataRowsTask.get_by_id(task_id)

    @staticmethod
    def create(dataset_id,
               data_rows: List[CreateDataRowInput]) -> List["DataRow"]:
        DataRow._check_sync_request_limits('create', len(data_rows))
        data_rows = DataRow._format_data_rows(data_rows)
        body = {
            'dataset_id': dataset_id,
            'data_rows': data_rows,
        }

        # TODO: Need to paginate sync call. Currently, 100 data rows is the limit
        data_rows = Session.post_request(f"{DATA_ROW_RESOURCE}", json=body)
        return [DataRow(data_row_json) for data_row_json in data_rows]

    @staticmethod
    def get_by_ids(ids: List[str],) -> Iterator["DataRow"]:
        return IdentifierPaginator(f"{DATA_ROW_RESOURCE}", DataRow, ids)

    @staticmethod
    def get_by_global_keys(global_keys: List[str],) -> Iterator["DataRow"]:
        return IdentifierPaginator(f"{DATA_ROW_RESOURCE}",
                                   DataRow,
                                   global_keys,
                                   identifiers_key='global_keys')

    @staticmethod
    def update_async(data_rows: List[UpdateDataRowInput]) -> UpdateDataRowsTask:
        for data_row in data_rows:
            if 'row_data' in data_row:
                data_row = DataRow._format_data_rows([data_row])[0]
        body = {'data_rows': data_rows}

        task_json = Session.post_request(f"{DATA_ROW_RESOURCE}/update-async",
                                         json=body)
        task_id = task_json.get(
            'taskId')  # TODO: change to snake_case from backend
        if task_id is None:
            raise LabelboxError(
                f"Failed to retrieve task information for `data_row.update_many()` async operation"
            )
        return UpdateDataRowsTask.get_by_id(task_id)

    @staticmethod
    def update(data_rows: List[UpdateDataRowInput]) -> List["DataRow"]:
        DataRow._check_sync_request_limits('update', len(data_rows))

        for data_row in data_rows:
            if 'row_data' in data_row:
                data_row = DataRow._format_data_rows([data_row])[0]
        body = {'data_rows': data_rows}
        data_rows = Session.patch_request(f"{DATA_ROW_RESOURCE}", json=body)
        return [DataRow(data_row_json) for data_row_json in data_rows]

    @staticmethod
    def delete_async(
            ids: Optional[List[str]] = None,
            global_keys: Optional[List[str]] = None) -> DeleteDataRowsTask:
        if ids:
            body = {'ids': ids}
        elif global_keys:
            body = {'global_keys': global_keys}

        task_json = Session.post_request(f"{DATA_ROW_RESOURCE}/delete-async",
                                         json=body)
        task_id = task_json.get(
            'taskId')  # TODO: change to snake_case from backend
        if task_id is None:
            raise LabelboxError(
                f"Failed to retrieve task information for `data_row.delete_many()` async operation"
            )
        return DeleteDataRowsTask.get_by_id(task_id)

    @staticmethod
    def delete(ids: Optional[List[str]] = None,
               global_keys: Optional[List[str]] = None) -> List[str]:
        if ids:
            DataRow._check_sync_request_limits('delete', len(ids))
            body = {'ids': ids}
        elif global_keys:
            DataRow._check_sync_request_limits('delete', len(global_keys))
            body = {'global_keys': global_keys}

        data_rows = Session.delete_request(f"{DATA_ROW_RESOURCE}", json=body)
        return data_rows
