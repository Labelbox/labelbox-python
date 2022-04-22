from typing import Generator
from labelbox.orm.db_object import DbObject, experimental
from labelbox.orm.model import Entity, Field, Relationship
from labelbox.exceptions import LabelboxError
from io import StringIO
import ndjson
import requests
import logging
import time

logger = logging.getLogger(__name__)


class Batch(DbObject):
    """ A Batch is a group of data rows submitted to a project for labeling

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

    # Relationships
    project = Relationship.ToOne("Project")
    created_by = Relationship.ToOne("User")

    def export_data_rows(self, timeout_seconds=120) -> Generator:
        """ Returns a generator that produces all data rows that are currently
        in this batch.

        Note: For efficiency, the data are cached for 30 minutes. Newly created data rows will not appear
        until the end of the cache period.

        Args:
            timeout_seconds (float): Max waiting time, in seconds.
        Returns:
            Generator that yields DataRow objects belonging to this batch.
        Raises:
            LabelboxError: if the export fails or is unable to download within the specified time.
        """
        id_param = "batchId"
        query_str = """mutation GetBatchDataRowsExportUrlPyApi($%s: ID!)
            {exportBatchDataRows(data:{batchId: $%s }) {downloadUrl createdAt status}}
        """ % (id_param, id_param)
        sleep_time = 2
        while True:
            res = self.client.execute(query_str, {id_param: self.uid})
            res = res["exportBatchDataRows"]
            if res["status"] == "COMPLETE":
                download_url = res["downloadUrl"]
                response = requests.get(download_url)
                response.raise_for_status()
                reader = ndjson.reader(StringIO(response.text))
                return (
                    Entity.DataRow(self.client, result) for result in reader)
            elif res["status"] == "FAILED":
                raise LabelboxError("Data row export failed.")

            timeout_seconds -= sleep_time
            if timeout_seconds <= 0:
                raise LabelboxError(
                    f"Unable to export data rows within {timeout_seconds} seconds."
                )

            logger.debug("Batch '%s' data row export, waiting for server...",
                         self.uid)
            time.sleep(sleep_time)
