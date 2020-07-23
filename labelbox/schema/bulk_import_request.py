import json
from pathlib import Path
from typing import Iterable

import ndjson

from labelbox import Client
from labelbox.exceptions import LabelboxError
from labelbox.orm import query
from labelbox.orm.db_object import DbObject
from labelbox.orm.model import Field
from labelbox.orm.model import Relationship
from labelbox.schema.enums import BulkImportRequestState
from labelbox.schema.enums import UploadedFileType


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

    @staticmethod
    def upload_local_predictions_file(
            client: Client, local_predictions_file_path: Path) -> str:
        """
        Uploads local NDJSON file containing predictions to Labelbox' object store
        and returns a URL of created file.

        Args:
            client (Client): The Labelbox client
            local_predictions_file_path (str): local NDJSON file containing predictions
        Returns:
            A URL of uploaded NDJSON file
        Raises:
            LabelboxError: if local file is not a valid NDJSON file
        """
        with local_predictions_file_path.open("rb") as f:
            try:
                data = ndjson.load(f)
            except ValueError:
                raise LabelboxError(
                    f"File {local_predictions_file_path} is not a valid ndjson file")
            else:
                return client.upload_data(
                    data, uploaded_file_type=UploadedFileType.PREDICTIONS)
