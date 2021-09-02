from typing import Dict, Iterable, Union
from pathlib import Path
import os

from labelbox.pagination import PaginatedCollection
from labelbox.schema.annotation_import import MEAPredictionImport
from labelbox.orm.query import results_query_part
from labelbox.orm.model import Field, Relationship
from labelbox.orm.db_object import DbObject


class ModelRun(DbObject):
    name = Field.String("name")
    updated_at = Field.DateTime("updated_at")
    created_at = Field.DateTime("created_at")
    created_by_id = Field.String("created_by_id", "createdBy")
    model_id = Field.String("model_id")

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
        predictions: Union[str, Path, Iterable[Dict]],
    ) -> 'MEAPredictionImport':  # type: ignore
        """ Uploads predictions to a new Editor project.
        Args:
            name (str): name of the AnnotationImport job
            predictions (str or Path or Iterable):
                url that is publicly accessible by Labelbox containing an
                ndjson file
                OR local path to an ndjson file
                OR iterable of annotation rows
        Returns:
            AnnotationImport
        """
        kwargs = dict(client=self.client, model_run_id=self.uid, name=name)
        if isinstance(predictions, str) or isinstance(predictions, Path):
            if os.path.exists(predictions):
                return MEAPredictionImport.create_from_file(
                    path=str(predictions), **kwargs)
            else:
                return MEAPredictionImport.create_from_url(url=str(predictions),
                                                           **kwargs)
        elif isinstance(predictions, Iterable):
            return MEAPredictionImport.create_from_objects(
                predictions=predictions, **kwargs)
        else:
            raise ValueError(
                f'Invalid predictions given of type: {type(predictions)}')

    def annotation_groups(self):
        query_str = """query modelRunPyApi($modelRunId: ID!, $from : String, $first: Int){
                annotationGroups(where: {modelRunId: {id: $modelRunId}}, after: $from, first: $first)
                {nodes{%s},pageInfo{endCursor}}
            }
        """ % (results_query_part(AnnotationGroup))
        return PaginatedCollection(
            self.client, query_str, {'modelRunId': self.uid},
            ['annotationGroups', 'nodes'],
            lambda client, res: AnnotationGroup(client, self.model_id, res),
            ['annotationGroups', 'pageInfo', 'endCursor'])

    def delete(self):
        """ Deletes specified model run.

        Returns:
            Query execution success.
        """
        ids_param = "ids"
        query_str = """mutation DeleteModelRunPyApi($%s: ID!) {
            deleteModelRuns(where: {ids: [$%s]})}""" % (ids_param, ids_param)
        self.client.execute(query_str, {ids_param: str(self.uid)})

    def delete_annotation_groups(self, data_row_ids):
        """ Deletes annotation groups by data row ids for a model run.

        Args:
            data_row_ids (list): List of data row ids to delete annotation groups.
        Returns:
            Query execution success.
        """
        model_run_id_param = "modelRunId"
        data_row_ids_param = "dataRowIds"
        query_str = """mutation DeleteModelRunDataRowsPyApi($%s: ID!, $%s: [ID!]!) {
            deleteModelRunDataRows(where: {modelRunId: $%s, dataRowIds: $%s})}""" % (
            model_run_id_param, data_row_ids_param, model_run_id_param,
            data_row_ids_param)
        self.client.execute(query_str, {
            model_run_id_param: self.uid,
            data_row_ids_param: data_row_ids
        })


class AnnotationGroup(DbObject):
    label_id = Field.String("label_id")
    model_run_id = Field.String("model_run_id")
    data_row = Relationship.ToOne("DataRow", False, cache=True)

    def __init__(self, client, model_id, *args, **kwargs):
        super().__init__(client, *args, **kwargs)
        self.model_id = model_id

    @property
    def url(self):
        app_url = self.client.app_url
        endpoint = f"{app_url}/models/{self.model_id}/{self.model_run_id}/AllDatarowsSlice/{self.uid}?view=carousel"
        return endpoint
