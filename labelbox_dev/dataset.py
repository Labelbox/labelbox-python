from typing import Optional, TypedDict

from labelbox_dev.entity import Entity
from labelbox_dev.session import Session

DATASET_RESOURCE = "datasets"


class CreateDatasetType(TypedDict):
    id: Optional[str]
    name: str
    description: Optional[str]


class UpdateDatasetType(TypedDict):
    name: Optional[str]
    description: Optional[str]


class Dataset(Entity):

    def __init__(self, json):
        super().__init__(json)
        self.from_json(json)

    def from_json(self, json) -> "Dataset":
        super().from_json(json)
        self.id = self.json['id']
        self.name = self.json['name']
        self.description = self.json['description']
        self.created_at = self.json['created_at']
        self.updated_at = self.json['updated_at']
        self.created_by_id = self.json['created_by_id']
        self.organization_id = self.json['organization_id']
        self.data_row_count = self.json['data_row_count']

        return self

    def update(self, dataset_update: UpdateDatasetType) -> "Dataset":
        dataset_json = Session.patch_request(f"{DATASET_RESOURCE}/{self.id}",
                                             json=dataset_update)
        return self.from_json(dataset_json)

    def delete(self) -> None:
        Session.delete_request(f"{DATASET_RESOURCE}/{self.id}")

    @staticmethod
    def create(dataset: CreateDatasetType):
        dataset_json = Session.post_request(f"{DATASET_RESOURCE}", json=dataset)
        return Dataset(dataset_json)

    @staticmethod
    def get_by_id(dataset_id: str):
        dataset_json = Session.get_request(f"{DATASET_RESOURCE}/{dataset_id}")
        return Dataset(dataset_json)
