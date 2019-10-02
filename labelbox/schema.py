from datetime import datetime, timezone
from enum import Enum, auto
import json
import logging
from multiprocessing.dummy import Pool as ThreadPool
import os
import time

from labelbox.exceptions import InvalidQueryError, ResourceNotFoundError
from labelbox.orm import query
from labelbox.orm.db_object import (DbObject, Updateable, Deletable,
                                    BulkDeletable)
from labelbox.orm.model import Field, Relationship
from labelbox.pagination import PaginatedCollection


""" Client-side object type definitions. """


logger = logging.getLogger(__name__)


class Project(DbObject, Updateable, Deletable):
    """ A Project is a container that includes a labeling frontend, an ontology,
    datasets and labels.
    """
    description = Field.String("description")
    updated_at = Field.DateTime("updated_at")
    created_at = Field.DateTime("created_at")
    setup_complete = Field.DateTime("setup_complete")
    last_activity_time = Field.DateTime("last_activity_time")
    auto_audit_number_of_labels = Field.Int("auto_audit_number_of_labels")
    auto_audit_percentage = Field.Float("auto_audit_percentage")

    # Relationships
    datasets = Relationship.ToMany("Dataset", True)
    created_by = Relationship.ToOne("User", False, "created_by")
    organization = Relationship.ToOne("Organization", False)
    reviews = Relationship.ToMany("Review", True)
    labeling_frontend = Relationship.ToOne("LabelingFrontend")
    labeling_frontend_options = Relationship.ToMany(
        "LabelingFrontendOptions", False, "labeling_frontend_options")
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

    def labels(self, datasets=None, order_by=None):
        query_string, params = query.project_labels(self, datasets, order_by)
        return PaginatedCollection(self.client, query_string, params,
                                   ["project", "labels"], Label)

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

    def review_metrics(self, net_score):
        """ Returns this Project's review metrics.
        Args:
            net_score (None or Review.NetScore): Indicates desired metric.
        Return:
            int, aggregation count of reviews for given net_score.
        """
        if net_score not in (None,) + tuple(Review.NetScore):
            raise InvalidQueryError("Review metrics net score must be either None "
                                    "or one of Review.NetScore values")
        query_str, params = query.project_review_metrics(self, net_score)
        res = self.client.execute(query_str, params)
        return res["data"]["project"]["reviewMetrics"]["labelAggregate"]["count"]

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
    """ A dataset is a collection of DataRows. For example, if you have a CSV with
    100 rows, you will have 1 Dataset and 100 DataRows.
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

    def data_row_for_external_id(self, external_id):
        """ Convenience method for getting a single `DataRow` belonging to this
        `Dataset` that has the given `external_id`.

        Args:
            external_id (str): External ID of the sought `DataRow`.

        Returns:
            A single `DataRow` with the given ID.

        Raises:
            labelbox.exceptions.ResourceNotFoundError: if there is no `DataRow`
                in this `DataSet` with the given external ID, or if there are
                multiple `DataRows` for it.
        """
        where = DataRow.external_id==external_id

        data_rows = self.data_rows(where=where)
        # Get at most two data_rows.
        data_rows = [row for row, _ in zip(data_rows, range(2))]

        if len(data_rows) != 1:
            raise ResourceNotFoundError(DataRow, where)

        return data_rows[0]


class DataRow(DbObject, Updateable, BulkDeletable):
    """ A DataRow represents a single piece of data. For example, if you have
    a CSV with 100 rows, you will have 1 Dataset and 100 DataRows.
    """
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
        query_str, params = query.create_metadata(meta_type, meta_value, self.uid)
        res = self.client.execute(query_str, params)
        return AssetMetadata(self.client, res["data"]["createAssetMetadata"])


class Label(DbObject, Updateable, BulkDeletable):
    """ Label represents an assessment on a DataRow. For example one label could
    contain 100 bounding boxes (annotations).
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.reviews.supports_filtering = False

    label = Field.String("label")
    seconds_to_label = Field.Float("seconds_to_label")
    agreement = Field.Float("agreement")
    benchmark_agreement = Field.Float("benchmark_agreement")
    is_benchmark_reference = Field.Boolean("is_benchmark_reference")

    project = Relationship.ToOne("Project")
    data_row = Relationship.ToOne("DataRow")
    reviews = Relationship.ToMany("Review", False)

    @staticmethod
    def bulk_delete(objects):
        BulkDeletable.bulk_delete(objects, False)

    def create_review(self, **kwargs):
        """ Creates a Review for this label.
        Kwargs:
            Review attributes. At a minimum a `Review.score` field
            value must be provided.
        """
        kwargs[Review.label.name] = self
        kwargs[Review.project.name] = self.project()
        return self.client._create(Review, kwargs)


class Review(DbObject, Deletable, Updateable):

    class NetScore(Enum):
        Negative = auto()
        Zero = auto()
        Positive = auto()

    updated_at = Field.DateTime("updated_at")
    created_at = Field.DateTime("created_at")
    score = Field.Float("score")

    created_by = Relationship.ToOne("User", False, "created_by")
    organization = Relationship.ToOne("Organization", False)
    project = Relationship.ToOne("Project", False)
    label = Relationship.ToOne("Label", False)


class AssetMetadata(DbObject):
    """ AssetMetadata is a datatype to provide extra context about an asset
    while labeling.
    """
    VIDEO = "VIDEO"
    IMAGE = "IMAGE"
    TEXT = "TEXT"

    meta_type = Field.String("meta_type")
    meta_value = Field.String("meta_value")


class User(DbObject):
    """ A User is a registered Labelbox user (for example you) associated with
    data they create or import and an Organization they belong to.
    """
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
    """ An Organization is a group of Users associated with data created by
    Users within that Organization. Typically all Users within an Organization
    have access to data created by any User in the same Organization.
    """

    # RelationshipManagers in Organization use the type in Query (and
    # not the source object) because the server-side does not support
    # filtering on ID in the query for getting a single organization.
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for relationship in self.relationships():
            getattr(self, relationship.name).filter_on_id = False

    updated_at = Field.DateTime("updated_at")
    created_at = Field.DateTime("created_at")
    name = Field.String("name")

    # Relationships
    users = Relationship.ToMany("User", False)
    projects = Relationship.ToMany("Project", True)
    webhooks = Relationship.ToMany("Webhook", False)


class Task(DbObject):
    """ Represents a server-side process that might take a longer time to process.
    Allows the Task state to be updated and checked on the client side.
    """
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
    """ Is a type representing an HTML / JavaScript UI that is used to generate
    labels. “Image Labeling” is the default Labeling Frontend that comes in every
    organization. You can create new labeling frontends for an organization.
    """
    name = Field.String("name")
    description = Field.String("description")
    iframe_url_path = Field.String("iframe_url_path")

    # TODO other fields and relationships
    projects = Relationship.ToMany("Project", True)


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
    """ Represents a server-side rule for sending notifications to a web-server
    whenever one of several predefined actions happens within a context of
    a Project or an Organization.
    """

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
        query_str, params = query.create_webhook(topics, url, secret, project)
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
