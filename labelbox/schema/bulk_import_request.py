import json
from typing import Iterable

from labelbox import Client
from labelbox.orm import query
from labelbox.orm.db_object import DbObject
from labelbox.orm.model import Field
from labelbox.orm.model import Relationship
from labelbox.schema.enums import BulkImportRequestState


class BulkImportRequest(DbObject):
    project = Relationship.ToOne("Project", False)
    name = Field.String("name")
    created_at = Field.DateTime("created_at")
    created_by = Relationship.ToOne("User", False, "created_by")
    input_file_url = Field.String("input_file_url")
    error_file_url = Field.String("error_file_url")
    status_file_url = Field.String("status_file_url")
    state = Field.Enum(BulkImportRequestState, "state")

    @staticmethod
    def create(
            client: Client, project_id: str, name: str,
            predictions: Iterable[dict]) -> 'BulkImportRequest':
        data_str = '\n'.join(json.dumps(prediction) for prediction in predictions)
        data = data_str.encode('utf-8')
        input_file_url = client.upload_data(data)
        query_str = """
        mutation CreateBulkImportRequestPyApi {
            createBulkImportRequest(data: {
                projectId: %s,
                name: %s,
                fileUrl: %s
            }) {
                %s
            }
        }
        """ % (
            project_id,
            name,
            input_file_url,
            query.results_query_part(BulkImportRequest)
        )
        bulk_import_request_kwargs = client.execute(query_str)["createBulkImportRequest"]
        return BulkImportRequest(client, bulk_import_request_kwargs)
