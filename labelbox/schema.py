from datetime import datetime, timezone
import json
import logging
from multiprocessing.dummy import Pool as ThreadPool
import os
import time

from labelbox.exceptions import InvalidQueryError
from labelbox.orm import query
from labelbox.orm.db_object import (DbObject, Updateable, Deletable,
                                    BulkDeletable)
from labelbox.orm.model import Field, Relationship


""" Client-side object type definitions. """


logger = logging.getLogger(__name__)


class Project(DbObject, Updateable, Deletable):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.labels.supports_filtering = False

    name = Field.String("name")
    description = Field.String("description")
    updated_at = Field.DateTime("updated_at")
    created_at = Field.DateTime("created_at")
    setup_complete = Field.DateTime("setup_complete")
    last_activity_time = Field.DateTime("last_activity_time")

    # Relationships
    datasets = Relationship.ToMany("Dataset", True)
    created_by = Relationship.ToOne("User", False, "created_by")
    organization = Relationship.ToOne("Organization", False)
    labeling_frontend = Relationship.ToOne("LabelingFrontend")
    labeling_frontend_options = Relationship.ToMany(
        "LabelingFrontendOptions", False, "labeling_frontend_options")
    labels = Relationship.ToMany("Label", True)
    labeling_parameter_overrides = Relationship.ToMany(
        "LabelingParameterOverride", False, "labeling_parameter_overrides")
    webhooks = Relationship.ToMany("Webhook", False)

    def create_label(self, **kwargs):
        """ Creates a label on this project.
        Kwargs:
            Label attributes. At the minimum the label `DataRow`
            and `Type` relationships and `label`, `seconds_to_label`
            fields.
        """
        # Copy-paste of Client._create code so we can inject
        # a connection to Type. Type objects are on their way to being
        # deprecated and we don't want the Py client lib user to know
        # about them. At the same time they're connected to a Label at
        # label creation in a non-standard way (connect via name).

        kwargs[Label.project] = self
        data = {Label.attribute(attr) if isinstance(attr, str) else attr:
                value.uid if isinstance(value, DbObject) else value
                for attr, value in kwargs.items()}

        query_str, params = query.create(Label, data)
        # Inject connection to Type
        query_str = query_str.replace("data: {",
                                      "data: {type: {connect: {name: \"Any\"}} ")
        res = self.client.execute(query_str, params)
        res = res["data"]["createLabel"]
        return Label(self.client, res)

    def export_labels(self, timeout_seconds=60):
        """ Calls the server-side Label exporting that generates a JSON
        payload, and returns the URL to that payload.
        Args:
            timeout_seconds (float): Max waiting time, in seconds.
        Return:
            URL of the data file with this Project's labels. If the server
                didn't generate during the `timeout_seconds` period, None
                is returned.
        """
        sleep_time = 2
        query_str, id_param = query.export_labels()
        while True:
            res = self.client.execute(query_str, {id_param: self.uid})[
                "data"]["exportLabels"]
            if not res["shouldPoll"]:
                return res["downloadUrl"]

            timeout_seconds -= sleep_time
            if timeout_seconds <= 0:
                return None

            logger.debug("Project '%s' label export, waiting for server...",
                         self.uid)
            time.sleep(sleep_time)

    # TODO Relationships
    # labeledDatasets
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

        labeling_frontend_options = self.client._create(
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

    def set_labeling_parameter_overrides(self, data):
        """ Adds labeling parameter overrides to this project.
        Args:
            data (iterable): An iterable of tuples. Each tuple must contain
                (DataRow, priority, numberOfLabels) for the new override.
        Return:
            bool indicating if the operation was a success.
        """
        query_str, params = query.set_labeling_parameter_overrides(self, data)
        res = self.client.execute(query_str, params)
        return res["data"]["project"]["setLabelingParameterOverrides"]["success"]

    def unset_labeling_parameter_overrides(self, data_rows):
        """ Removes labeling parameter overrides to this project.
        Args:
            data_rows (iterable): An iterable of DataRows.
        Return:
            bool indicating if the operation was a success.
        """
        query_str, params = query.unset_labeling_parameter_overrides(self, data_rows)
        res = self.client.execute(query_str, params)
        return res["data"]["project"]["unsetLabelingParameterOverrides"]["success"]


class Dataset(DbObject, Updateable, Deletable):
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

        return self.client._create(DataRow, kwargs)

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
        file_upload_thread_count = 20

        def upload_if_necessary(item):
            if isinstance(item, str):
                with open(item, "rb") as f:
                    item_data = f.read()
                item_url = self.client.upload_data(item_data)
                # Convert item from str into a dict so it gets processed
                # like all other dicts.
                item = {DataRow.row_data: item_url,
                        DataRow.external_id: item}
            return item

        with ThreadPool(file_upload_thread_count) as thread_pool:
            items = thread_pool.map(upload_if_necessary, items)

        def convert_item(item):
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


class DataRow(DbObject, Updateable, BulkDeletable):
    external_id = Field.String("external_id")
    row_data = Field.String("row_data")
    updated_at = Field.DateTime("updated_at")
    created_at = Field.DateTime("created_at")

    # Relationships
    dataset = Relationship.ToOne("Dataset")
    created_by = Relationship.ToOne("User", False, "created_by")
    organization = Relationship.ToOne("Organization", False)
    labels = Relationship.ToMany("Label", True)
    metadata = Relationship.ToMany("AssetMetadata", False, "metadata")

    @staticmethod
    def bulk_delete(objects):
        BulkDeletable.bulk_delete(objects, True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.metadata.supports_filtering = False
        self.metadata.supports_sorting = False

    def create_metadata(self, meta_type, meta_value):
        """ Creates an asset metadata for this DataRow.
        Args:
            meta_type (str): Asset metadata type, must be one of:
                VIDEO, IMAGE, TEXT.
            meta_value (str): Asset metadata value.
        Return:
            AssetMetadata DB object.
        """
        query_str, params = query.create_metadata(
            AssetMetadata, meta_type, meta_value, self.uid)
        res = self.client.execute(query_str, params)
        return AssetMetadata(self.client, res["data"]["createAssetMetadata"])


class Label(DbObject, Updateable, BulkDeletable):
    label = Field.String("label")
    seconds_to_label = Field.Float("seconds_to_label")
    agreement = Field.Float("agreement")
    benchmark_agreement = Field.Float("benchmark_agreement")
    is_benchmark_reference = Field.Boolean("is_benchmark_reference")

    project = Relationship.ToOne("Project")
    data_row = Relationship.ToOne("DataRow")

    @staticmethod
    def bulk_delete(objects):
        BulkDeletable.bulk_delete(objects, False)


class AssetMetadata(DbObject):
    VIDEO = "VIDEO"
    IMAGE = "IMAGE"
    TEXT = "TEXT"

    meta_type = Field.String("meta_type")
    meta_value = Field.String("meta_value")


class User(DbObject):
    updated_at = Field.DateTime("updated_at")
    created_at = Field.DateTime("created_at")
    email = Field.String("email")
    name = Field.String("nickname")
    nickname = Field.String("name")
    intercom_hash = Field.String("intercom_hash")
    picture = Field.String("picture")
    is_viewer = Field.Boolean("is_viewer")
    is_external_user = Field.Boolean("is_external_user")

    # Relationships
    organization = Relationship.ToOne("Organization")
    created_tasks = Relationship.ToMany("Task", False, "created_tasks")
    projects = Relationship.ToMany("Project", False)

    # TODO other attributes


class Organization(DbObject):
    updated_at = Field.DateTime("updated_at")
    created_at = Field.DateTime("created_at")
    name = Field.String("name")

    # Relationships
    users = Relationship.ToMany("User", False)
    projects = Relationship.ToMany("Project", True)
    webhooks = Relationship.ToMany("Webhook", False)


class Task(DbObject):
    updated_at = Field.DateTime("updated_at")
    created_at = Field.DateTime("created_at")
    name = Field.String("name")
    status = Field.String("status")
    completion_percentage = Field.Float("completion_percentage")

    # Relationships
    created_by = Relationship.ToOne("User", False, "created_by")
    organization = Relationship.ToOne("Organization")

    def refresh(self):
        """ Refreshes Task data from the server. """
        tasks = list(self._user.created_tasks(where=Task.uid == self.uid))
        if len(tasks) != 1:
            raise ResourceNotFoundError(Task, task_id)
        for field in self.fields():
            setattr(self, field.name, getattr(tasks[0], field.name))

    def wait_till_done(self, timeout_seconds=60):
        """ Waits until the task is completed. Periodically queries the server
        to update the task attributes.
        Args:
            timeout_seconds (float): Maximum time this method can block, in
                seconds. Defaults to one minute.
        """
        check_frequency = 2 # frequency of checking, in seconds
        while True:
            if self.status != "IN_PROGRESS":
                return
            sleep_time_seconds = min(check_frequency, timeout_seconds)
            logger.debug("Task.wait_till_done sleeping for %.2f seconds" %
                         sleep_time_seconds)
            if sleep_time_seconds <= 0:
                break
            timeout_seconds -= check_frequency
            time.sleep(sleep_time_seconds)
            self.refresh()


class LabelingFrontend(DbObject):
    name = Field.String("name")
    description = Field.String("description")
    iframe_url_path = Field.String("iframe_url_path")

    # TODO other fields and relationships


class LabelingFrontendOptions(DbObject):
    customization_options = Field.String("customization_options")

    project = Relationship.ToOne("Project")
    labeling_frontend = Relationship.ToOne("LabelingFrontend")
    organization = Relationship.ToOne("Organization")


class LabelingParameterOverride(DbObject):
    priority = Field.Int("priority")
    number_of_labels = Field.Int("number_of_labels")


# Webhook is Updateable, but with using custom GraphQL.
class Webhook(DbObject):

    # Status
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    REVOKED = "REVOKED"

    # Topic
    LABEL_CREATED = "LABEL_CREATED"
    LABEL_UPDATED = "LABEL_UPDATED"
    LABEL_DELETED = "LABEL_DELETED"

    updated_at = Field.DateTime("updated_at")
    created_at = Field.DateTime("created_at")
    url = Field.String("url")
    topics = Field.String("topics")
    status = Field.String("status")

    @staticmethod
    def create(client, topics, url, secret, project):
        query_str, params = query.create_webhook(Webhook, topics, url, secret,
                                                 project)
        res = client.execute(query_str, params)
        return Webhook(client, res["data"]["createWebhook"])

    created_by = Relationship.ToOne("User", False, "created_by")
    organization = Relationship.ToOne("Organization")
    project = Relationship.ToOne("Project")

    def update(self, topics=None, url=None, status=None):
        # Webhook has a custom `update` function due to custom types
        # in `status` and `topics` fields.
        query_str, params = query.edit_webhook(self, topics, url, status)
        res = self.client.execute(query_str, params)
        res = res["data"]["updateWebhook"]
        self._set_field_values(res)
