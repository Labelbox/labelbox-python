import json
from multiprocessing.dummy import Pool as ThreadPool
import os

from labelbox.exceptions import InvalidQueryError, ResourceNotFoundError, InvalidAttributeError
from labelbox.orm.db_object import DbObject, Updateable, Deletable
from labelbox.orm.model import Entity, Field, Relationship


class Dataset(DbObject, Updateable, Deletable):
    """ A Dataset is a collection of DataRows.

    Attributes:
        name (str)
        description (str)
        updated_at (datetime)
        created_at (datetime)

        projects (Relationship): `ToMany` relationship to Project
        data_rows (Relationship): `ToMany` relationship to DataRow
        created_by (Relationship): `ToOne` relationship to User
        organization (Relationship): `ToOne` relationship to Organization

    """
    name = Field.String("name")
    description = Field.String("description")
    updated_at = Field.DateTime("updated_at")
    created_at = Field.DateTime("created_at")

    # Relationships
    projects = Relationship.ToMany("Project", True)
    data_rows = Relationship.ToMany("DataRow", False)
    created_by = Relationship.ToOne("User", False, "created_by")
    organization = Relationship.ToOne("Organization", False)

    def create_data_row(self, **kwargs):
        """ Creates a single DataRow belonging to this dataset.

        >>> dataset.create_data_row(row_data="http://my_site.com/photos/img_01.jpg")

        Args:
            **kwargs: Key-value arguments containing new `DataRow` data. At a minimum,
                must contain `row_data`.

        Raises:
            InvalidQueryError: If `DataRow.row_data` field value is not provided
                in `kwargs`.
            InvalidAttributeError: in case the DB object type does not contain
                any of the field names given in `kwargs`.

        """
        DataRow = Entity.DataRow
        if DataRow.row_data.name not in kwargs:
            raise InvalidQueryError(
                "DataRow.row_data missing when creating DataRow.")

        # If row data is a local file path, upload it to server.
        row_data = kwargs[DataRow.row_data.name]
        if os.path.exists(row_data):
            kwargs[DataRow.row_data.name] = self.client.upload_file(row_data)

        kwargs[DataRow.dataset.name] = self

        return self.client._create(DataRow, kwargs)

    def create_data_rows(self, items):
        """ Creates multiple DataRow objects based on the given `items`.

        Each element in `items` can be either a `str` or a `dict`. If
        it is a `str`, then it is interpreted as a local file path. The file
        is uploaded to Labelbox and a DataRow referencing it is created.
        If an item is a `dict`, then it should map `DataRow` fields (or their
        names) to values. At the minimum an `item` passed as a `dict` must
        contain a `DataRow.row_data` key and value.

        >>> dataset.create_data_rows([
        >>>     {DataRow.row_data:"http://my_site.com/photos/img_01.jpg"},
        >>>     "path/to/file2.jpg"
        >>>     ])

        Args:
            items (iterable of (dict or str)): See above for details.

        Returns:
            Task representing the data import on the server side. The Task
            can be used for inspecting task progress and waiting until it's done.

        Raises:
            InvalidQueryError: If the `items` parameter does not conform to
                the specification above or if the server did not accept the
                DataRow creation request (unknown reason).
            ResourceNotFoundError: If unable to retrieve the Task for the
                import process. This could imply that the import failed.
            InvalidAttributeError: If there are fields in `items` not valid for
                a DataRow.
        """
        file_upload_thread_count = 20
        DataRow = Entity.DataRow

        def upload_if_necessary(item):
            if isinstance(item, str):
                item_url = self.client.upload_file(item)
                # Convert item from str into a dict so it gets processed
                # like all other dicts.
                item = {DataRow.row_data: item_url, DataRow.external_id: item}
            return item

        with ThreadPool(file_upload_thread_count) as thread_pool:
            items = thread_pool.map(upload_if_necessary, items)

        def convert_item(item):
            # Convert string names to fields.
            item = {
                key if isinstance(key, Field) else DataRow.field(key): value
                for key, value in item.items()
            }

            if DataRow.row_data not in item:
                raise InvalidQueryError(
                    "DataRow.row_data missing when creating DataRow.")

            invalid_keys = set(item) - set(DataRow.fields())
            if invalid_keys:
                raise InvalidAttributeError(DataRow, invalid_keys)

            # Item is valid, convert it to a dict {graphql_field_name: value}
            # Need to change the name of DataRow.row_data to "data"
            return {
                "data" if key == DataRow.row_data else key.graphql_name: value
                for key, value in item.items()
            }

        # Prepare and upload the desciptor file
        data = json.dumps([convert_item(item) for item in items])
        descriptor_url = self.client.upload_data(data)

        # Create data source
        dataset_param = "datasetId"
        url_param = "jsonUrl"
        query_str = """mutation AppendRowsToDatasetPyApi($%s: ID!, $%s: String!){
            appendRowsToDataset(data:{datasetId: $%s, jsonFileUrl: $%s}
            ){ taskId accepted } } """ % (dataset_param, url_param,
                                          dataset_param, url_param)
        res = self.client.execute(query_str, {
            dataset_param: self.uid,
            url_param: descriptor_url
        })
        res = res["appendRowsToDataset"]
        if not res["accepted"]:
            raise InvalidQueryError(
                "Server did not accept DataRow creation request")

        # Fetch and return the task.
        task_id = res["taskId"]
        user = self.client.get_user()
        task = list(user.created_tasks(where=Entity.Task.uid == task_id))
        # Cache user in a private variable as the relationship can't be
        # resolved due to server-side limitations (see Task.created_by)
        # for more info.
        if len(task) != 1:
            raise ResourceNotFoundError(Entity.Task, task_id)
        task = task[0]
        task._user = user
        return task

    def data_row_for_external_id(self, external_id):
        """ Convenience method for getting a single `DataRow` belonging to this
        `Dataset` that has the given `external_id`.

        Args:
            external_id (str): External ID of the sought `DataRow`.

        Returns:
            A single `DataRow` with the given ID.

        Raises:
            labelbox.exceptions.ResourceNotFoundError: If there is no `DataRow`
                in this `DataSet` with the given external ID, or if there are
                multiple `DataRows` for it.
        """
        DataRow = Entity.DataRow
        where = DataRow.external_id == external_id

        data_rows = self.data_rows(where=where)
        # Get at most two data_rows.
        data_rows = [row for row, _ in zip(data_rows, range(2))]

        if len(data_rows) != 1:
            raise ResourceNotFoundError(DataRow, where)

        return data_rows[0]
