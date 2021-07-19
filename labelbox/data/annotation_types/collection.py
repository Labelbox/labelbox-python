from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Iterable, List, Any
from uuid import uuid4

from pydantic import BaseModel

from labelbox.data.annotation_types.label import Label
from labelbox.orm.model import Entity


class LabelCollection(BaseModel):
    data: Iterable[Label]

    def assign_schema_ids(self, ontology_builder):
        """
        Based on an ontology:
            - Checks to make sure that the feature names exist in the ontology
            - Updates the names to match the ontology.
        """
        for label in self.data:
            for annotation in label.annotations:
                annotation.assign_schema_ids(ontology_builder)

    def create_dataset(self, client, dataset_name, signer, max_concurrency=20):
        external_ids = set()
        for label in self.data:
            if label.data.external_id is None:
                label.data.external_id = uuid4()
            else:
                if label.data.external_id in external_ids:
                    raise ValueError(
                        f"External ids must be unique for bulk uploading. Found {label.data.exeternal_id} more than once."
                    )
            external_ids.add(label.data.external_id)
        labels = self.create_urls_for_data(signer,
                                           max_concurrency=max_concurrency)
        dataset = client.create_dataset(name=dataset_name)
        upload_task = dataset.create_data_row(
            {Entity.DataRow.row_data: label.data.url for label in labels})
        upload_task.wait_til_done()

        data_rows = {
            data_row.external_id: data_row.uid
            for data_row in dataset.export_data_rows()
        }
        for label in self.data:
            data_row = data_rows[label.data.external_id]
            label.data.uid = data_row.uid

    def create_urls_for_masks(self, signer, max_concurrency=20):
        """
        Creates a data row id for each data row that needs it. If the data row exists then it skips the row.
        TODO: Add error handling..
        """
        futures = {}
        with ThreadPoolExecutor(max_workers=max_concurrency) as executor:
            for label in self.data:
                futures[executor.submit(label.create_url_for_masks)] = label
            for future in as_completed(futures):
                # Yields the label. But this function modifies the objects to have updated urls.
                yield futures[future]
                del futures[future]

    def create_urls_for_data(self, signer, max_concurrency=20):
        """
        TODO: Add error handling..
        """
        futures = {}
        with ThreadPoolExecutor(max_workers=max_concurrency) as executor:
            for label in self.data:
                futures[executor.submit(label.create_url_for_data)] = label
            for future in as_completed(futures):
                yield futures[future]
                del futures[future]
