import os
from typing import Any, Iterator, List, Optional, Union

from labelbox_dev.entity import Entity
from labelbox_dev.exceptions import LabelboxError
from labelbox_dev.session import Session
from labelbox_dev.task import GetDataRowsTask, CreateDataRowsTask, DeleteDataRowsTask, UpdateDataRowsTask
from labelbox_dev.types import TypedDict
from labelbox_dev.pagination import IdentifierPaginator

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


class UpdateDataRowsWithIdType(TypedDict):
    id: str
    global_key: Optional[str]
    external_id: Optional[str]
    row_data: Optional[str]


class UpdateDataRowType(TypedDict):
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

    def update(self, data_row_update: UpdateDataRowType) -> "DataRow":
        data_row_json = Session.patch_request(f"{DATA_ROW_RESOURCE}/{self.id}",
                                              json=data_row_update)
        return self.from_json(data_row_json)

    def delete(self) -> None:
        Session.delete_request(f"{DATA_ROW_RESOURCE}/{self.id}")

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
    def create_one(dataset_id, data_row: CreateDataRowType):
        data_row = DataRow._format_data_rows([data_row])[0]
        body = {'dataset_id': dataset_id, 'data_row': data_row}
        data_row_json = Session.post_request(f"{DATA_ROW_RESOURCE}", json=body)
        return DataRow(data_row_json)

    @staticmethod
    def create(dataset_id,
               data_rows: List[CreateDataRowType],
               run_async: bool = False):
        data_rows = DataRow._format_data_rows(data_rows)

        body = {
            'dataset_id': dataset_id,
            'data_rows': data_rows,
            'run_async': run_async
        }
        if run_async:
            task_json = Session.post_request(f"{DATA_ROW_RESOURCE}/bulkcreate",
                                             json=body)
            task_id = task_json.get(
                'taskId')  # TODO: change to snake_case from backend

            if task_id is None:
                raise LabelboxError(
                    f"Failed to retrieve task information for `data_row.create()` async operation"
                )
            return CreateDataRowsTask.get_by_id(task_id)

        # TODO: Need to paginate sync call. Currently, 100 data rows is the limit
        data_rows = Session.post_request(f"{DATA_ROW_RESOURCE}/bulkcreate",
                                         json=body)
        return [DataRow(data_row_json) for data_row_json in data_rows]

    @staticmethod
    def get_by_id(id: str):
        data_row_json = Session.get_request(f"{DATA_ROW_RESOURCE}/{id}")
        return DataRow(data_row_json)

    @staticmethod
    def get_by_global_key(global_key: str):
        params = {'is_global_key': True}
        data_row_json = Session.get_request(f"{DATA_ROW_RESOURCE}/{global_key}",
                                            params=params)
        return DataRow(data_row_json)

    @staticmethod
    def get_by_ids(
            ids: List[str],
            run_async: bool = False
    ) -> Union[Iterator["DataRow"], GetDataRowsTask]:
        body = {'keys': ids, 'run_async': run_async}

        if run_async:
            task_json = Session.post_request(f"{DATA_ROW_RESOURCE}/bulkget",
                                             json=body)
            # TODO: change to snake_case from backend
            task_id = task_json.get('taskId')

            if task_id is None:
                raise LabelboxError(
                    f"Failed to retrieve task information for `data_row.get_by_ids()` async operation"
                )
            return GetDataRowsTask.get_by_id(task_id)

        return IdentifierPaginator(f"{DATA_ROW_RESOURCE}", DataRow, ids)

    @staticmethod
    def get_by_global_keys(
            global_keys: List[str],
            run_async: bool = False
    ) -> Union[Iterator["DataRow"], GetDataRowsTask]:
        body = {
            'keys': global_keys,
            'is_global_key': True,
            'run_async': run_async
        }
        if run_async:
            task_json = Session.post_request(f"{DATA_ROW_RESOURCE}/bulkget",
                                             json=body)
            # TODO: change to snake_case from backend
            task_id = task_json.get('taskId')

            if task_id is None:
                raise LabelboxError(
                    f"Failed to retrieve task information for `data_row.get_by_global_keys()` async operation"
                )
            return GetDataRowsTask.get_by_id(task_id)

        return IdentifierPaginator(f"{DATA_ROW_RESOURCE}",
                                   DataRow,
                                   global_keys,
                                   identifiers_key='global_keys')

    @staticmethod
    def update_many(data_rows: List[UpdateDataRowsWithIdType],
                    run_async: bool = False):
        for data_row in data_rows:
            if 'row_data' in data_row:
                data_row = DataRow._format_data_rows([data_row])[0]

        body = {'data_rows': data_rows, 'run_async': run_async}
        if run_async:
            task_json = Session.post_request(f"{DATA_ROW_RESOURCE}/bulkupdate",
                                             json=body)
            task_id = task_json.get(
                'taskId')  # TODO: change to snake_case from backend

            if task_id is None:
                raise LabelboxError(
                    f"Failed to retrieve task information for `data_row.update_many()` async operation"
                )
            return UpdateDataRowsTask.get_by_id(task_id)

        data_rows = Session.post_request(f"{DATA_ROW_RESOURCE}/bulkupdate",
                                         json=body)
        return [DataRow(data_row_json) for data_row_json in data_rows]

    @staticmethod
    def delete_many(ids: Optional[List[str]] = None,
                    global_keys: Optional[List[str]] = None,
                    run_async: bool = False):
        body = {'run_async': run_async}
        if ids:
            body.update({'ids': ids})
        if global_keys:
            body.update({'global_keys': global_keys})

        if run_async:
            task_json = Session.post_request(f"{DATA_ROW_RESOURCE}/bulkdelete",
                                             json=body)
            task_id = task_json.get(
                'taskId')  # TODO: change to snake_case from backend

            if task_id is None:
                raise LabelboxError(
                    f"Failed to retrieve task information for `data_row.delete_many()` async operation"
                )
            return DeleteDataRowsTask.get_by_id(task_id)

        data_rows = Session.post_request(f"{DATA_ROW_RESOURCE}/bulkdelete",
                                         json=body)
        return data_rows
