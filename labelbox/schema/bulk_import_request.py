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

    @classmethod
    def create_from_url(
            cls, client: Client, project_id: str, name: str,
            url: str) -> 'BulkImportRequest':
        query_str = """
        mutation CreateBulkImportRequestPyApi {
            createBulkImportRequest(data: {
                projectId: "%s",
                name: "%s",
                fileUrl: "%s"
            }) {
                %s
            }
        }
        """ % (
            project_id,
            name,
            url,
            query.results_query_part(BulkImportRequest)
        )
        bulk_import_request_kwargs = client.execute(query_str)["createBulkImportRequest"]
        return BulkImportRequest(client, bulk_import_request_kwargs)
