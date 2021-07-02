

from labelbox.data.annotation_types.annotation import Label
from typing import Dict, List, Any
from labelbox import Entity



class AnnotationCollection:
    data : List[Label]

    # TODO: Move these functions to serializer classes that accepts an annotation collection as an argument
    # Otherwise this class might get quite big as we add different functionality

    def upload_to_dataset(self, dataset: "Entity.Dataset"):
        """
        TODO:
        - Support bulk creation of dataset. If data does not exist in labelbox this is how to add it
        - Upload all data using dataset.create_data_rows()
        - Export all data using dataset.export_data_rows()
        - Update all label.data.data_row_ref.id and data.url with the row_data by matching on external_id
        """
        ...

    def link_features_to_labelbox(self, project: "Entity.Project"):
        """
        TODO:
        - feature schemas are optional as long as a name exists.
        - This function should add all feature schema ids based on an ontology
        - All features that don't have valid schemas should be
        - This should apply to everything from features, nested features, to options
        """

    def to_mal_ndjsons(self) -> List[Dict[str, Any]]:
        return [ndjson for ndjsons in self.data.to_mal_ndjsons() for ndjson in ndjsons]


    def upload_to_mal(self) -> None:
        ndjsons = [ndjson for ndjsons in self.data.to_mal_ndjsons() for ndjson in ndjsons]
        #TODO: Complete implementation
