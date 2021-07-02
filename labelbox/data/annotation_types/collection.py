

from labelbox.data.annotation_types.annotation import Annotation, Label
from typing import Dict, List
from labelbox import Entity



class AnnotationCollection:
    # it needs to upload to data rows if that doesn't exist....
    data : List[Label]
    # We need to differentiate data that links to labelbox and data that does not..

    def upload_to_dataset(self, dataset: "Entity.Dataset"):
        """
        - Support bulk creation of dataset
        - Upload all data using dataset.create_data_rows()
        - Export all data using dataset.export_data_rows()
        - Update all label.data.data_row_ref.id and data.url with the row_data by matching on external_id
        """
        ...

    def to_mal_ndjsons(self):
        return [ndjson for ndjsons in self.data.to_mal_ndjsons() for ndjson in ndjsons]


    def upload_to_mal(self):
        ndjsons = [ndjson for ndjsons in self.data.to_mal_ndjsons() for ndjson in ndjsons]





















