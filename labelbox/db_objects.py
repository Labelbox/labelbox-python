from datetime import datetime, timezone
import logging
import json
import os
import time

from labelbox import query, utils
from labelbox.paginated_collection import PaginatedCollection
from labelbox.schema import Field, DbObject, Relationship


""" Defines client-side objects representing database content. """


logger = logging.getLogger(__name__)


class RelationshipManager:
    """ Manages relationships object fetching and updates for a DB object
    instance. There is one RelationshipManager for each relationship in
    each DB object instance.
    """

    def __init__(self, source, relationship):
        """Args:
            source (DbObject subclass instance): The object that's the source
                of the relationship.
            relationship (labelbox.schema.Relationship): The relationship
                schema descriptor object.
        """
        self.source = source
        self.relationship = relationship
        self.destination_type = next(
            t for t in MutableDbObject.__subclasses__()
            if t.__name__.split(".")[-1] == relationship.destination_type_name)

    def __call__(self, *args, **kwargs ):
        """ Forwards the call to either `_to_many` or `_to_one` methods,
        depending on relationship type. """
        if self.relationship.relationship_type == Relationship.Type.ToMany:
            return self._to_many(*args, **kwargs)
        else:
            return self._to_one(*args, **kwargs)

    def _to_many(self, where=None, order_by=None):
        """ Returns an iterable over the destination relationship objects.
        Args:
            where (None, Comparison or LogicalExpression): Filtering clause.
            order_by (None or (Field, Field.Order)): Ordering clause.
        Return:
            iterable over destination DbObject instances.
        """
        rel = self.relationship
        if rel.filter_deleted:
            not_deleted = self.destination_type.deleted == False
            where = not_deleted if where is None else where & not_deleted

        query_string, params = query.relationship(
            self.source, rel.name,
            self.destination_type,
            True, where, order_by)
        return PaginatedCollection(
            self.source.client, query_string, params,
            [utils.camel_case(type(self.source).type_name()),
             rel.graphql_name],
            self.destination_type)

    def _to_one(self):
        """ Returns the relationship destination object. """
        rel = self.relationship

        query_string, params = query.relationship(
            self.source, rel.name, self.destination_type, False, None, None)
        result = self.source.client.execute(query_string, params)["data"]
        result = result[utils.camel_case(type(self.source).type_name())]
        result = result[rel.graphql_name]
        return self.destination_type(self.source.client, result)

    def connect(self, other):
        """ Connects source object of this manager to the `other` object. """
        query_string, params = query.update_relationship(
            self.source, other, self.relationship.name, "connect")
        self.source.client.execute(query_string, params)

    def disconnect(self, other):
        """ Disconnects source object of this manager from the `other` object. """
        query_string, params = query.update_relationship(
            self.source, other, self.relationship.name, "disconnect")
        self.source.client.execute(query_string, params)


class MutableDbObject(DbObject):
    """ A DbObject subtype that should be used as a base class for all DbObject
    types that contain relationships. Ensures that during initialization of
    a DB object instance the appropriate `RelationshipManager` instances are
    created and injected. """

    def __init__(self, *args, **kwargs):
        """ Forwards all arguments to DbObject initializer. Then adds a
        RelationshipManager as attribute for each relationship of this
        DbObject's type. """
        super().__init__(*args, **kwargs)

        for relationship in type(self).relationships():
            setattr(self, relationship.name,
                    RelationshipManager(self, relationship))

    def update(self, **kwargs):
        """ Updates this DB object with new values. Values should be
        passed as key-value arguments with field names as keys:
            >>> db_object.update(name="New name", title="A title")

        Kwargs:
            Key-value arguments defining which fields should be updated
            for which values. Keys must be field names in this DB object's
            type.
        Raise:
            InvalidAttributeError: if there exists a key in `kwargs`
                that's not a field in this object type.
        """
        values = {self.field(name): value for name, value in kwargs.items()}
        invalid_fields = set(values) - set(self.fields())
        if invalid_fields:
            raise InvalidAttributeError(type(self), invalid_fields)

        query_string, params = query.update_fields(self, values)
        res = self.client.execute(query_string, params)
        res = res["data"]["update%s" % utils.title_case(self.type_name())]
        self._set_field_values(res)

    def delete(self):
        """ Deletes this DB object from the DB (server side). After
        a call to this you should not use this DB object anymore.
        """
        query_string, params = query.delete(self)
        self.client.execute(query_string, params)


class Project(MutableDbObject):
    name = Field.String("name")
    description = Field.String("description")
    updated_at = Field.DateTime("updated_at")
    created_at = Field.DateTime("created_at")
    setup_complete = Field.DateTime("setup_complete")

    # Relationships
    datasets = Relationship.ToMany("Dataset", True)
    created_by = Relationship.ToOne("User", False, "created_by")
    labeling_frontend = Relationship.ToOne("LabelingFrontend")
    labeling_frontend_options = Relationship.ToMany(
        "LabelingFrontendOptions", False, "labeling_frontend_options")

    # TODO Relationships
    # organization
    # createdBy
    # datasets
    # labeledDatasets
    # labels
    # ...a lot more, define which are required for v0.1

    # TODO Mutable (fetched) attributes
    # ...many, define which are required for v0.1

    def setup(self, labeling_frontend, labeling_frontend_options):
        """ Finalizes the Project setup.
        Args:
            labeling_frontend (LabelingFrontend): The labeling frontend to use.
            labeling_frontend_options (dict or str): Labeling frontend options,
                a.k.a. project ontology. If given a `dict` it will be converted
                to `str` using `json.dumps`.
        """
        organization = self.client.get_organization()
        if not isinstance(labeling_frontend_options, str):
            labeling_frontend_options = json.dumps(labeling_frontend_options)

        labeling_frontend_options = self.client.create(
            LabelingFrontendOptions,
            {LabelingFrontendOptions.project: self,
             LabelingFrontendOptions.labeling_frontend: labeling_frontend,
             LabelingFrontendOptions.customization_options: labeling_frontend_options,
             LabelingFrontendOptions.organization: organization
            }
        )

        self.labeling_frontend.connect(labeling_frontend)
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        self.update(setup_complete=timestamp)


class Dataset(MutableDbObject):
    name = Field.String("name")
    updated_at = Field.DateTime("updated_at")
    created_at = Field.DateTime("created_at")

    # Relationships
    projects = Relationship.ToMany("Project", True)
    data_rows = Relationship.ToMany("DataRow", False)

    def create_data_row(self, **kwargs):
        """ Creates a single DataRow belonging to this dataset.
        Kwargs:
            Key-value arguments containing new `DataRow` data.
            At a minimum they must contain `row_data`. The value for
            `row_data` is a string. If it's a path to an existing local
            file then it's uploaded to Labelbox's server. Otherwise it's
            treated as an external URL.
        Raises:
            InvalidQueryError: If `DataRow.row_data` field value is not provided
                in `data`.
                any of the field names given in `data`.
            InvalidAttributeError: in case the DB object type does not contain
                any of the field names given in `data`.

        """
        if DataRow.row_data.name not in kwargs:
            raise InvalidQueryError(
                "DataRow.row_data missing when creating DataRow.")

        # If row data is a local file path, upload it to server.
        row_data = kwargs[DataRow.row_data.name]
        if os.path.exists(row_data):
            kwargs[DataRow.row_data.name] = self.client.upload_data(row_data)

        kwargs[DataRow.dataset.name] = self

        return self.client.create(DataRow, kwargs)

    def create_data_rows(self, items):
        """ Creates multiple DataRow objects based on the given items.
        Each element in `items` can be either a `str` or a `dict`. If
        it's a `str`, then it's interpreted as a file path. The file
        is uploaded to Labelbox and a DataRow referencing it is created.
        If an item is a `dict`, then it should map `DataRow` fields (or their
        names) to values. At the minimum it must contain a `DataRow.row_data`
        key and value.

        Args:
            items (iterable of (dict or str)): See above for details.
        Return:
            Task representing the data import on the server side. The Task
            can be used for inspecting task progress and waiting until it's done.
        Raise:
            InvalidQueryError: if the `items` parameter does not conform to
                the specification above.
            MalformedRequestError: if the server did not accept the DataRow
                creation request.
            ResourceNotFoundError: if unable to retrieve the Task based on the
                task_id of the import process. This could imply that the import
                failed.
            InvalidAttributeError: if there are fields in `items` not valid for
                a DataRow.
        """
        def convert_item(item):
            if isinstance(item, str):
                with open(item, "rb") as f:
                    item_data = f.read()
                item_url = self.client.upload_data(item_data)
                # Convert item from str into a dict so it gets processed
                # like all other dicts.
                item = {DataRow.row_data: item_url,
                        DataRow.external_id: item}

            # Convert string names to fields.
            item = {key if isinstance(key, Field) else DataRow.field(key): value
                    for key, value in item.items()}

            if DataRow.row_data not in item:
                raise InvalidQueryError(
                    "DataRow.row_data missing when creating DataRow.")

            invalid_keys = set(item) - set(DataRow.fields())
            if invalid_keys:
                raise InvalidAttributeError(DataRow, invalid_fields)

            # Item is valid, convert it to a dict {graphql_field_name: value}
            # Need to change the name of DataRow.row_data to "data"
            return {"data" if key == DataRow.row_data else key.graphql_name: value
                    for key, value in item.items()}

        # Prepare and upload the desciptor file
        data = json.dumps([convert_item(item) for item in items])
        descriptor_url = self.client.upload_data(data)

        # Create data source
        res = self.client.execute(*query.create_data_rows(self.uid, descriptor_url))
        res = res["data"]["appendRowsToDataset"]

        if not res["accepted"]:
            raise MalformedRequestError(
                "Server did not accept DataRow creation request", data)

        # Fetch and return the task.
        task_id = res["taskId"]
        user = self.client.get_user()
        task = list(user.created_tasks(where=Task.uid == task_id))
        # Cache user in a private variable as the relationship can't be
        # resolved due to server-side limitations (see Task.created_by)
        # for more info.
        if len(task) != 1:
            raise ResourceNotFoundError(Task, task_id)
        task = task[0]
        task._user = user
        return task

    # TODO Relationships
    # organization
    # createdBy
    # projects
    # dataRows

    # TODO Fetched attributes
    # rowCount
    # createdLabelCount


class DataRow(MutableDbObject):
    external_id = Field.String("external_id")
    row_data = Field.String("row_data")
    updated_at = Field.DateTime("updated_at")
    created_at = Field.DateTime("created_at")

    # Relationships
    dataset = Relationship.ToOne("Dataset")

    # TODO other attributes


class User(MutableDbObject):
    updated_at = Field.DateTime("updated_at")
    created_at = Field.DateTime("created_at")
    email = Field.String("email")
    name = Field.String("nickname")
    nickname = Field.String("name")

    # Relationships
    organization = Relationship.ToOne("Organization")
    created_tasks = Relationship.ToMany("Task", False, "created_tasks")
    projects = Relationship.ToMany("Project", False)

    # TODO other attributes


class Organization(MutableDbObject):
    updated_at = Field.DateTime("updated_at")
    created_at = Field.DateTime("created_at")
    name = Field.String("name")

    # Relationships
    users = Relationship.ToMany("User", False)

    # TODO other attributes


class Task(MutableDbObject):

    updated_at = Field.DateTime("updated_at")
    created_at = Field.DateTime("created_at")
    name = Field.String("name")
    status = Field.String("status")
    completion_percentage = Field.Float("completion_percentage")

    # Relationships

    # TODO "created_by" can't be treated as a relationship because there's
    # currently no way on the server to make a query starting from
    # a single task.
    # created_by = Relationship.ToOne("User", "createdBy")

    def refresh(self):
        """ Refreshes Task data from the server. """
        tasks = list(self._user.created_tasks(where=Task.uid == self.uid))
        if len(tasks) != 1:
            raise ResourceNotFoundError(Task, task_id)
        for field in self.fields():
            setattr(self, field.name, getattr(tasks[0], field.name))

    def wait_till_done(self, timeout_seconds=60, check_frequency_seconds=1):
        """ Waits until the task is completed. Periodically queries the server
        to update the task attributes.
        Args:
            timeout_seconds (float): Maximum time this method can block, in
                seconds. Defaults to one minute.
            check_frequency_seconds (float): Sleep time between two checks,
                in seconds. Defaults to one second.
        """
        while True:
            if self.status != "IN_PROGRESS":
                return
            sleep_time_seconds = min(check_frequency_seconds, timeout_seconds)
            logger.debug("Task.wait_till_done sleeping for %.2f seconds" %
                         sleep_time_seconds)
            if sleep_time_seconds <= 0:
                break
            timeout_seconds -= check_frequency_seconds
            time.sleep(sleep_time_seconds)
            self.refresh()

    # TODO other attributes


class LabelingFrontend(MutableDbObject):
    name = Field.String("name")
    description = Field.String("description")
    iframe_url_path = Field.String("iframe_url_path")

    # TODO other fields and relationships


class LabelingFrontendOptions(MutableDbObject):
    customization_options = Field.String("customization_options")

    project = Relationship.ToOne("Project")
    labeling_frontend = Relationship.ToOne("LabelingFrontend")
    organization = Relationship.ToOne("Organization")
