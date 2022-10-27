from typing import List, Optional, TypedDict, Union
from labelbox_dev.entity import Entity
from labelbox_dev.session import Session

DATA_ROW_RESOURCE = "data-rows"


class AttachmentsType(TypedDict):
    type: str
    value: str
    name: str


class MetadataType(TypedDict):
    schema_id: str
    value: Union[str, int]


class CreateDataRowType(TypedDict):
    id: Optional[str]
    global_key: Optional[str]
    external_id: Optional[str]
    row_data: str
    attachments: List[AttachmentsType]
    metadata: List[MetadataType]


class UpdateDataRowType(TypedDict):
    global_key: Optional[str]
    external_id: Optional[str]
    row_data: Optional[str]


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


def create(dataset_id, data_row: CreateDataRowType):
    create_data_row_input = {'dataset_id': dataset_id, 'data_row': data_row}
    # TODO: upload if row_data is local file
    # TODO: accept metadata and attachments as part of the request
    data_row_json = Session.post_request(f"{DATA_ROW_RESOURCE}",
                                         json=create_data_row_input)
    return DataRow(data_row_json)


def create_many(dataset_id, data_rows: List[CreateDataRowType]):
    # TODO: Bulk creation and handling local files
    pass


class DataRow(Entity):

    def __init__(self, json):
        super().__init__(json)
        self.from_json(json)

    def from_json(self, json) -> "DataRow":
        self.json = json
        self.id = json['id']
        self.global_key = json['global_key']
        self.external_id = json['external_id']
        self.created_at = json['created_at']
        self.updated_at = json['updated_at']
        self.row_data = json['row_data']
        self.dataset_id = json['dataset_id']
        self.created_by_id = json['created_by_id']
        self.organization_id = json['organization_id']

        return self

    def metadata(self):
        # TODO: Get metadata
        pass

    def attachments(self):
        # TODO: Get attachments
        pass

    def media_attributes(self):
        # TODO: Get media attributes
        pass

    def delete(self) -> bool:
        # TODO: Implement on backend
        is_deleted = Session.delete_request(f"{DATA_ROW_RESOURCE}/{self.id}")
        return is_deleted

    def update(self, data_row_update: UpdateDataRowType) -> "DataRow":
        data_row_json = Session.patch_request(f"{DATA_ROW_RESOURCE}/{self.id}",
                                              json=data_row_update)
        return self.from_json(data_row_json)
