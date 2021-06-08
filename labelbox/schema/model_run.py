from labelbox.schema.annotation_import import AnnotationImport, MALPredictionImport, MEAPredictionImport
from pathlib import Path
from typing import Dict, Iterable, Union
from labelbox.orm.model import Field, Relationship
from labelbox.orm.db_object import DbObject


class ModelRun(DbObject):
    name = Field.String("name")
    updated_at = Field.DateTime("updated_at")
    created_at = Field.DateTime("created_at")
    created_by_id = Field.String("created_by_id", "createdBy")

    def upsert_labels(self, label_ids):

        if len(label_ids) < 1:
            raise ValueError("Must provide at least one label id")

        query_str = """mutation upsertModelRunLabelsPyApi($modelRunId: ID!, $labelIds : [ID!]!) {
          upsertModelRunLabels(where : { id : $modelRunId}, data : {labelIds: $labelIds})}
          """
        res = self.client.execute(query_str, {
            'modelRunId': self.uid,
            'labelIds': label_ids
        })
        # TODO: Return a task
        return True

    def add_predictions(
            self,
            name: str,
            annotations: Union[str, Path, Iterable[Dict]],
            validate: bool = True) -> 'MEAPredictionImport':  # type: ignore
        """ Uploads annotations to a new Editor project.
        Args:
            name (str): name of the AnnotationImport job
            annotations (str or Path or Iterable):
                url that is publicly accessible by Labelbox containing an
                ndjson file
                OR local path to an ndjson file
                OR iterable of annotation rows
            validate (bool):
                Whether or not to validate the payload before uploading.
        Returns:
            AnnotationImport
        """
        kwargs = dict(client=self.client,
                      model_run_id=self.uid,
                      name=name,
                      predictions=annotations)
        if isinstance(annotations, str) or isinstance(annotations, Path):
            return MEAPredictionImport.create_from_file(**kwargs)
        elif isinstance(annotations, Iterable):
            return MEAPredictionImport.create_from_objects(**kwargs)
        else:
            raise ValueError(
                f'Invalid annotations given of type: {type(annotations)}')
