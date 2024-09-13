from typing import Generator, TYPE_CHECKING

from labelbox.orm.db_object import DbObject, experimental
from labelbox.orm import query
from labelbox.orm.model import Entity, Field, Relationship
from labelbox.exceptions import LabelboxError, ResourceNotFoundError
from io import StringIO
from labelbox import parser
import requests
import logging
import time
import warnings

if TYPE_CHECKING:
    from labelbox import Project

logger = logging.getLogger(__name__)


class Batch(DbObject):
    """A Batch is a group of data rows submitted to a project for labeling

    Attributes:
        name (str)
        created_at (datetime)
        updated_at (datetime)
        deleted (bool)

        project (Relationship): `ToOne` relationship to Project
        created_by (Relationship): `ToOne` relationship to User

    """

    name = Field.String("name")
    created_at = Field.DateTime("created_at")
    updated_at = Field.DateTime("updated_at")
    size = Field.Int("size")
    consensus_settings = Field.Json("consensus_settings_json")

    # Relationships
    created_by = Relationship.ToOne("User")

    def __init__(
        self, client, project_id, *args, failed_data_row_ids=[], **kwargs
    ):
        super().__init__(client, *args, **kwargs)
        self.project_id = project_id
        self._failed_data_row_ids = failed_data_row_ids

    def project(self) -> "Project":  # type: ignore
        """Returns Project which this Batch belongs to

        Raises:
            LabelboxError: if the project is not found
        """
        query_str = """query getProjectPyApi($projectId: ID!) {
            project(
                where: {id: $projectId}){
                    %s
                }}""" % query.results_query_part(Entity.Project)
        params = {"projectId": self.project_id}
        response = self.client.execute(query_str, params)

        if response is None:
            raise ResourceNotFoundError(Entity.Project, params)

        return Entity.Project(self.client, response["project"])

    def remove_queued_data_rows(self) -> None:
        """Removes remaining queued data rows from the batch and labeling queue.

        Args:
            batch (Batch): Batch to remove queued data rows from
        """

        project_id_param = "projectId"
        batch_id_param = "batchId"
        self.client.execute(
            """mutation RemoveQueuedDataRowsFromBatchPyApi($%s: ID!, $%s: ID!) {
            project(where: {id: $%s}) { removeQueuedDataRowsFromBatch(batchId: $%s) { id } }
        }"""
            % (
                project_id_param,
                batch_id_param,
                project_id_param,
                batch_id_param,
            ),
            {project_id_param: self.project_id, batch_id_param: self.uid},
            experimental=True,
        )

    def delete(self) -> None:
        """Deletes the given batch.

        Note: Batch deletion for batches that has labels is forbidden.

        Args:
            batch (Batch): Batch to remove queued data rows from
        """

        project_id_param = "projectId"
        batch_id_param = "batchId"
        self.client.execute(
            """mutation DeleteBatchPyApi($%s: ID!, $%s: ID!) {
            project(where: {id: $%s}) { deleteBatch(batchId: $%s) { deletedBatchId } }
        }"""
            % (
                project_id_param,
                batch_id_param,
                project_id_param,
                batch_id_param,
            ),
            {project_id_param: self.project_id, batch_id_param: self.uid},
            experimental=True,
        )

    def delete_labels(self, set_labels_as_template=False) -> None:
        """Deletes labels that were created for data rows in the batch.

        Args:
            batch (Batch): Batch to remove queued data rows from
            set_labels_as_template (bool): When set to true, the deleted labels will be kept as templates.
        """

        project_id_param = "projectId"
        batch_id_param = "batchId"
        type_param = "type"
        res = self.client.execute(
            """mutation DeleteBatchLabelsPyApi($%s: ID!, $%s: ID!, $%s: DeleteBatchLabelsType!) {
            project(where: {id: $%s}) { deleteBatchLabels(batchId: $%s, data:{ type: $%s }) { deletedLabelIds } }
        }"""
            % (
                project_id_param,
                batch_id_param,
                type_param,
                project_id_param,
                batch_id_param,
                type_param,
            ),
            {
                project_id_param: self.project_id,
                batch_id_param: self.uid,
                type_param: "RequeueDataWithLabelAsTemplate"
                if set_labels_as_template
                else "RequeueData",
            },
            experimental=True,
        )
        return res

    # modify this function to return an empty list if there are no failed data rows

    @property
    def failed_data_row_ids(self):
        if self._failed_data_row_ids is None:
            self._failed_data_row_ids = []

        return (x for x in self._failed_data_row_ids)
